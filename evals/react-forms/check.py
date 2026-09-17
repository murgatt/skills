#!/usr/bin/env python3
"""Grade one eval run against the react-forms conventions.

Usage: python3 evals/react-forms/check.py <eval_name> <run_dir>
  e.g. python3 evals/react-forms/check.py build-invite-form-from-scratch \
         evals/react-forms/workspace/iteration-2/build-invite-form-from-scratch/with_skill

Evals live outside the skill folder on purpose: skills are symlinked into
~/.claude/skills, so anything inside skills/react-forms/ ships with the skill.
When running an eval, copy each fixture ALONE into its own run folder - an
agent that finds the conforming fixture next to its input copies its style,
which silently inflates the baseline.
Writes <run_dir>/grading.json with {expectations: [{text, passed, evidence}]}.
"""
import json, re, sys
from pathlib import Path

SRC_EXT = {".ts", ".tsx"}


def load(run_dir: Path):
    out = run_dir / "outputs"
    files = {}
    if out.is_dir():
        for p in sorted(out.rglob("*")):
            if p.is_file() and p.suffix in SRC_EXT:
                files[str(p.relative_to(out))] = p.read_text(errors="replace")
    return files


def generic_args(src: str, head: str):
    """Return the top-level generic arguments of the first `head` occurrence."""
    i = src.find(head)
    if i < 0:
        return None
    j = i + len(head)
    depth, cur, args = 1, "", []
    while j < len(src) and depth:
        c = src[j]
        if c == "<":
            depth += 1
        elif c == ">":
            depth -= 1
            if depth == 0:
                break
        if depth == 1 and c == ",":
            args.append(cur.strip()); cur = ""
        else:
            cur += c
        j += 1
    args.append(cur.strip())
    return [a for a in args if a]


class Grader:
    def __init__(self, files):
        self.files = files
        self.blob = "\n".join(files.values())
        self.results = []

    def add(self, text, passed, evidence):
        self.results.append({"text": text, "passed": bool(passed), "evidence": str(evidence)[:400]})

    def has(self, pattern, flags=0):
        m = re.search(pattern, self.blob, flags)
        return m.group(0).strip() if m else None

    def where(self, pattern, flags=0):
        return [n for n, c in self.files.items() if re.search(pattern, c, flags)]

    # --- shared conventions -------------------------------------------------
    def core(self, form_stem=None):
        schemas = [n for n in self.files if n.endswith(".schema.ts")]
        self.add("Schema lives in its own file suffixed .schema.ts",
                 bool(schemas), schemas or "no *.schema.ts file found")

        kebab = [n for n in schemas if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*\.schema\.ts", Path(n).name)]
        self.add("Schema filename is kebab-case",
                 bool(schemas) and len(kebab) == len(schemas),
                 f"kebab-case: {kebab} / all: {[Path(n).name for n in schemas]}")

        const = self.has(r"export const [a-z][A-Za-z0-9]*Schema\s*=")
        self.add("Schema const is camelCase ending in `Schema`", const, const or "not found")

        infer = self.where(r"z\.infer<")
        self.add("z.infer is not used", not infer, infer or "absent")

        self.add("Both z.input<> and z.output<> are used",
                 self.has(r"z\.input<") and self.has(r"z\.output<"),
                 f"z.input={bool(self.has(r'z.input<'))} z.output={bool(self.has(r'z.output<'))}")

        ti = self.has(r"export type [A-Z][A-Za-z0-9]*FormInput\b")
        to = self.has(r"export type [A-Z][A-Za-z0-9]*FormOutput\b")
        self.add("Types named ...FormInput / ...FormOutput", ti and to, f"{ti} | {to}")

        self.add("mode: 'onTouched' is set",
                 self.has(r"mode:\s*['\"]onTouched['\"]"),
                 self.has(r"mode:\s*['\"][a-zA-Z]+['\"]") or "no mode option found")

        self.add("zodResolver is wired up", self.has(r"zodResolver\("), self.has(r"zodResolver\(") or "absent")

        args = generic_args(self.blob, "useForm<")
        self.add("useForm uses all three generics <Input, Context, Output>",
                 args is not None and len(args) == 3,
                 args if args is not None else "no explicit useForm<> generics")

        hooks = [n for n in self.files if re.fullmatch(r".*use[A-Z][A-Za-z0-9]*\.ts", n)]
        self.add("useForm call is isolated in a use…Form.ts hook file",
                 any("useForm<" in self.files[n] or "useForm(" in self.files[n] for n in hooks),
                 hooks or "no use*.ts hook file")

        # form element + submit wiring
        form_tag = self.has(r"<form[^>]*onSubmit=\{", re.S)
        self.add("Submission is wired on the <form> element via handleSubmit",
                 bool(form_tag) and bool(self.has(r"handleSubmit\(")),
                 form_tag or "no <form onSubmit={...}> found")

        # An id on <form> is only justified when a submit button sits outside it.
        outside_btn = self.has(r"<[A-Za-z][^>]*\sform=[\"'{]", re.S)
        form_id = self.has(r"<form[^>]*\bid=", re.S)
        if outside_btn:
            self.add("Outside submit button is matched by an id on the form element",
                     bool(form_id), form_id or "button has a form attribute but <form> has no id")
        else:
            self.add("No gratuitous id on the form element (no outside submit button)",
                     not form_id, form_id or "absent, as expected")

        self.add('Submit button declares type="submit"',
                 self.has(r'type=["\']submit["\']'), self.has(r'type=["\']submit["\']') or "absent")

        bad_click = self.has(r"onClick=\{[^}]*handleSubmit\(")
        self.add("Submit is not wired through the button's onClick", not bad_click, bad_click or "absent")

        bad_disabled = self.has(r"disabled=\{[^}]*\b(isValid|isDirty)\b")
        self.add("Button is not disabled by validity or dirtiness", not bad_disabled, bad_disabled or "absent")

        onsub = self.has(r"onSubmit[?]?:\s*\([^)]*\)\s*=>")
        self.add("onSubmit arrives as a typed prop", onsub, onsub or "no onSubmit prop signature")

        # Scope this to the form itself: a parent page/panel is *supposed* to own the
        # mutation, so only files living beside the schema (or named like the form) count.
        form_dirs = {str(Path(n).parent) for n in self.files if n.endswith(".schema.ts")}
        def is_form_file(n):
            if form_dirs:
                return str(Path(n).parent) in form_dirs
            return bool(re.search(r"(Form\.tsx|Form\.ts|[Ss]chema\.ts)$", n))
        fetches = [n for n in self.where(r"\b(fetch|axios)\s*\(") if is_form_file(n)]
        self.add("Form component itself does not perform the network call",
                 not fetches, fetches or "absent (parent page/panel excluded)")

        # watch / formState
        viol = []
        for pat, label in [(r"formState\s*:\s*\{", "destructured formState:{...}"),
                           (r"const\s*\{[^}]*\bwatch\b[^}]*\}", "destructured watch"),
                           (r"\.\s*watch\s*\(", "called .watch()")]:
            hit = self.has(pat)
            if hit:
                viol.append(f"{label}: {hit}")
        self.add("watch / formState are never destructured from useForm or useFormContext",
                 not viol, viol or "clean")

        self.add("Uses useFormState and/or useWatch",
                 self.has(r"\buseFormState\(") or self.has(r"\buseWatch\("),
                 f"useFormState={bool(self.has(r'useFormState'))} useWatch={bool(self.has(r'useWatch'))}")

        hook_exports = []
        for n, c in self.files.items():
            if re.fullmatch(r".*use[A-Z][A-Za-z0-9]*\.ts", n) and re.search(r"export\s+type\b", c):
                hook_exports.append(n)
        self.add("Hook file exports no type aliases (they belong in a .types.ts)",
                 not hook_exports, hook_exports or "clean")

        types_files = [n for n in self.files if n.endswith(".types.ts")]
        field_comps = [n for n in self.files if re.search(r"[A-Z][A-Za-z0-9]*Field\.tsx$", n)]
        self.add("No .types.ts file unless a field component imports from it",
                 not types_files or bool(field_comps),
                 f"types files={types_files} field components={field_comps}")

        fp = self.where(r"\bFormProvider\b")
        self.add("No FormProvider (not needed at this depth)", not fp, fp or "absent")

        if form_stem:
            dirs = {str(Path(n).parent) for n in self.files}
            cluster = [d for d in dirs if any(Path(n).parent == Path(d) and n.endswith(".schema.ts") for n in self.files)
                       and any(Path(n).parent == Path(d) and n.endswith(".tsx") for n in self.files)]
            self.add("Component, hook and schema are colocated in one folder",
                     bool(cluster), f"folders holding both a .tsx and a .schema.ts: {cluster or 'none'}")


def grade(eval_name, run_dir: Path):
    files = load(run_dir)
    g = Grader(files)
    if not files:
        g.add("Run produced source files", False, "no .ts/.tsx files under outputs/")
        return g.results

    if eval_name == "build-invite-form-from-scratch":
        g.core(form_stem="InviteMember")
        g.add("Role field defaults to 'member'",
              g.has(r"\.default\(\s*['\"]member['\"]\s*\)") or g.has(r"role:\s*['\"]member['\"]"),
              g.has(r"\.default\([^)]*\)") or "no default found")
        cap = bool(g.has(r"max\(\s*(?:500|[A-Z][A-Z0-9_]*)"))
        opt = bool(g.has(r"\.optional\(\)"))
        g.add("Message is optional and capped at 500", cap and opt,
              "max(500)={} optional()={}".format(cap, opt))

    elif eval_name == "extend-form-with-dependent-field":
        g.core(form_stem="ShippingAddress")
        field_comps = [n for n in files if re.search(r"ShippingAddressForm[A-Z][A-Za-z0-9]*Field\.tsx$", n)]
        g.add("Dependent field extracted to <FormName><Field>.tsx in the same folder",
              bool(field_comps), field_comps or [n for n in files if n.endswith('.tsx')])
        child = "\n".join(files[n] for n in field_comps)
        g.add("Field component receives `control` as a prop",
              re.search(r"control\s*:", child) if child else False,
              (re.search(r"control\s*:[^;\n]*", child).group(0) if child and re.search(r"control\s*:", child) else "no control prop"))
        g.add("Field component does not take the whole form object",
              not re.search(r"\bform\s*:\s*(UseFormReturn|[A-Z][A-Za-z0-9]*Form)\b", child or ""),
              "clean" if child else "n/a")
        alias_files = [n for n, c in files.items() if "ShippingAddressFormControl" in c and "export type" in c]
        g.add("Control alias is declared in a .types.ts file, not the hook",
              bool(alias_files) and all(n.endswith(".types.ts") for n in alias_files),
              alias_files or "no exported Control alias found")
        g.add("Country dependency is read with useWatch on control (field name is the author's choice)",
              re.search(r"useWatch\(\s*\{[^}]*name:\s*['\"]country", g.blob, re.S | re.I),
              g.has(r"useWatch\(\s*\{[^}]*\}", re.S) or "no useWatch")
        main = files.get("ShippingAddressForm/ShippingAddressForm.tsx", "")
        g.add("Parent form component does not subscribe to country itself",
              "useWatch" not in main, "parent is clean" if "useWatch" not in main else "useWatch found in parent")
        g.add("country added to the existing schema file",
              any("country" in c for n, c in files.items() if n.endswith(".schema.ts")),
              [n for n in files if n.endswith('.schema.ts')])

    elif eval_name == "fix-nonconforming-form":
        g.core(form_stem="ProfileSettings")
        for fld in ["displayName", "email", "bio", "newsletter"]:
            g.add(f"Behaviour preserved: `{fld}` field still present", fld in g.blob, "present" if fld in g.blob else "MISSING")

    return g.results


if __name__ == "__main__":
    name, rd = sys.argv[1], Path(sys.argv[2])
    res = grade(name, rd)
    (rd / "grading.json").write_text(json.dumps({"expectations": res}, indent=2))
    p = sum(r["passed"] for r in res)
    print(f"{rd}: {p}/{len(res)}")
    for r in res:
        if not r["passed"]:
            print(f"   FAIL  {r['text']}  <- {r['evidence'][:110]}")
