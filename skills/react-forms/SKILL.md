---
name: react-forms
description: How forms are built in a React codebase — folder layout and colocation, schema file naming and input/output typing, validation mode, submit wiring, when to extract a field into its own component, how to subscribe to values and form state, and when form context is allowed. Current stack is react-hook-form with Zod. Use this skill whenever you create, extend, refactor, or review ANY React form — including when the user mentions a form, a useForm call, a Zod schema for form input, validation rules or error messages, adding or extracting a form field, wiring a submit handler, or fixing form typing — even if they never say "react-hook-form" or "zod" by name.
---

# React forms

These are the house rules for every form in a React codebase. Apply them when you build a new form and when you touch an existing one. If a file you are editing already breaks a rule, bring the parts you touch into line — don't silently rewrite files the task didn't ask about.

**Current stack:** react-hook-form v7, zod v4, @hookform/resolvers v5. Check `package.json` first. If the installed versions differ in a way that changes the API below, adapt the code and say so in your summary rather than emitting something that won't compile.

## The shape at a glance

Every form is a folder named after the form, in PascalCase. Three files are mandatory; other files join them only when something in the form actually needs them.

```
InviteMemberForm/
  InviteMemberForm.tsx                 # main component — owns <form>, takes onSubmit as a prop
  useInviteMemberForm.ts               # the useForm call, and nothing else
  invite-member-form.schema.ts         # the zod schema + Input/Output types
```

One stem, three spellings, applied mechanically: folder `InviteMemberForm` → component `InviteMemberForm.tsx` → hook `useInviteMemberForm.ts` → schema `invite-member-form.schema.ts`. The schema file is the only kebab-case one, because it is the only module that is neither a component nor a hook.

Three more files exist only when earned:

- `InviteMemberFormTeamField.tsx` — a field that meets the extraction test (rule 5)
- `invite-member-form.types.ts` — form-level types that a _separate_ file needs, such as a `Control` alias (rule 5)
- `useInviteMemberFormContext.ts` — only when `FormProvider` is justified (rule 7)

### The canonical form

```ts
// invite-member-form.schema.ts
import { z } from "zod";

export const inviteMemberFormSchema = z.object({
  email: z.email("Enter a valid email address"),
  message: z.string().trim().max(500).optional(),
  role: z.enum(["member", "admin"]).default("member"),
});

export type InviteMemberFormInput = z.input<typeof inviteMemberFormSchema>;
export type InviteMemberFormOutput = z.output<typeof inviteMemberFormSchema>;
```

```ts
// useInviteMemberForm.ts
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import type { DefaultValues } from "react-hook-form";

import { inviteMemberFormSchema } from "./invite-member-form.schema";
import type {
  InviteMemberFormInput,
  InviteMemberFormOutput,
} from "./invite-member-form.schema";

type UseInviteMemberFormOptions = {
  defaultValues?: DefaultValues<InviteMemberFormInput>;
};

export function useInviteMemberForm({
  defaultValues,
}: UseInviteMemberFormOptions = {}) {
  return useForm<InviteMemberFormInput, unknown, InviteMemberFormOutput>({
    defaultValues,
    mode: "onTouched",
    resolver: zodResolver(inviteMemberFormSchema),
  });
}
```

```tsx
// InviteMemberForm.tsx
import { useFormState } from "react-hook-form";
import type { DefaultValues } from "react-hook-form";

import { useInviteMemberForm } from "./useInviteMemberForm";
import type {
  InviteMemberFormInput,
  InviteMemberFormOutput,
} from "./invite-member-form.schema";

type InviteMemberFormProps = {
  defaultValues?: DefaultValues<InviteMemberFormInput>;
  onSubmit: (values: InviteMemberFormOutput) => void | Promise<void>;
};

export function InviteMemberForm({
  defaultValues,
  onSubmit,
}: InviteMemberFormProps) {
  const { control, handleSubmit, register } = useInviteMemberForm({
    defaultValues,
  });
  const { errors, isSubmitting } = useFormState({ control });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <label htmlFor="invite-member-email">Email</label>
      <input
        aria-describedby={
          errors.email ? "invite-member-email-error" : undefined
        }
        aria-invalid={!!errors.email}
        id="invite-member-email"
        type="email"
        {...register("email")}
      />
      {errors.email && (
        <p id="invite-member-email-error" role="alert">
          {errors.email.message}
        </p>
      )}

      {/* role and message follow the same pattern */}

      <button disabled={isSubmitting} type="submit">
        {isSubmitting ? "Sending…" : "Send invite"}
      </button>
    </form>
  );
}
```

`noValidate` is on the form element on purpose: native browser validation would block the submit event before react-hook-form ever runs, which breaks the rule that clicking submit always surfaces _our_ validation messages.

### `defaultValues` only when the form is prefilled

This form takes `defaultValues` because it is also used to edit an existing invite (rule 1). A form that only ever starts empty leaves it out everywhere: the hook takes no argument and the component has no `defaultValues` prop.

```ts
// useInviteMemberForm.ts — a create-only form
export function useInviteMemberForm() {
  return useForm<InviteMemberFormInput, unknown, InviteMemberFormOutput>({
    mode: "onTouched",
    resolver: zodResolver(inviteMemberFormSchema),
  });
}
```

Initial values that never come from the caller — a select that should show a preset — are still written as the `defaultValues` option inside the hook. They don't justify a hook argument.

### The examples use plain HTML on purpose

Real forms here are usually built with the project's UI component library, and sometimes with a `Field` / `FormField` component that owns the label, the error message and the accessibility wiring. Which components exist varies by project, so these examples stick to native elements to keep the rules readable. Before writing fields, open an existing form in the codebase and build with the same components. Every rule in this skill still applies; rule 5 decides between `register` and `Controller` based on what those components accept.

When the project has no such component and you write plain elements, wire them the way the canonical form does:

- `htmlFor` on each `label`, matching the `id` of its control
- `aria-invalid` on the control, and `aria-describedby` pointing at its error while there is one
- `role="alert"` on the error message, so it is announced when it appears

A project `Field` component usually does all of that for you, which is a good reason to use one when it exists. If that component reads the form from React context instead of taking `control`, `FormProvider` is justified — see rule 7.

---

## 1. Colocation, and what gets reused

Everything belonging to one form lives in that form's folder. A schema that exists to validate a form is part of that form, not a shared type module.

**To reuse a form, reuse the whole component.** The hook and the schema are implementation details of one form; they are not a public API.

This matters because a shared schema or a shared hook looks harmless right up until the second consumer needs one extra field, one different default, or one relaxed rule. At that point you either fork it anyway or bolt on flags that make both call sites harder to read. The component boundary is the one that holds: it accepts `onSubmit` — plus `defaultValues` when the form can be prefilled — which is everything a second consumer legitimately needs to vary.

```tsx
// ✅ the same form, used for create and for edit
<InviteMemberForm onSubmit={createInvite} />
<InviteMemberForm defaultValues={invite} onSubmit={updateInvite} />
```

```ts
// ❌ don't import another form's internals
import { inviteMemberFormSchema } from "../InviteMemberForm/invite-member-form.schema";
import { useInviteMemberForm } from "../InviteMemberForm/useInviteMemberForm";
```

If two forms genuinely share a _validation primitive_ (a password strength rule, a phone format), extract that primitive — `passwordSchema`, `phoneSchema` — to a shared module and compose it inside each form's own schema. Sharing a field rule is fine; sharing a whole form schema is not.

Whether the folder gets an `index.ts` barrel is not this skill's call — look at the sibling folders and follow whatever the codebase already does. If you do add one, export only the form component, so the hook and schema stay private by construction.

## 2. The schema file

- File name: kebab-case, suffixed `.schema.ts`.
- Schema const: camelCase, full form stem plus `Schema` — `inviteMemberFormSchema`.
- Types: PascalCase, `…FormInput` and `…FormOutput`, inferred with `z.input` and `z.output` **explicitly**.
- Both types live in the same file as the schema.

```ts
// ✅
export const inviteMemberFormSchema = z.object({
  /* … */
});
export type InviteMemberFormInput = z.input<typeof inviteMemberFormSchema>;
export type InviteMemberFormOutput = z.output<typeof inviteMemberFormSchema>;
```

```ts
// ❌ z.infer hides the gap between what the user types and what you get back
export type InviteMemberFormValues = z.infer<typeof inviteMemberFormSchema>;
```

`z.infer` is an alias for `z.output`. Using it isn't wrong so much as it's _silent_: it gives you the parsed shape under a name that sounds like it covers both sides, so the moment a field has `.default()`, `.transform()`, `.coerce`, or `.optional()` with a fallback, the form's actual value type and the submitted value type quietly diverge and you get a type error you have to debug backwards. Naming both ends makes the divergence visible and gives `useForm` the two types it needs.

Keep this file pure zod — schema and the two inferred types. Types that need `react-hook-form` belong in the types file described in rule 5.

Two zod v4 specifics worth getting right:

- Prefer the top-level string formats — `z.email()`, `z.url()`, `z.uuid()`, `z.iso.date()`. The method forms like `z.string().email()` are deprecated in v4.
- `.default(…)` must be assignable to the **output** type in v4 (this reversed from v3; `.prefault()` restores the old behaviour). Note that a schema default does _not_ pre-fill the input — zod applies it at parse time, react-hook-form renders from `defaultValues`. If a field should show a value before the user touches it, put it in the hook's `defaultValues` as well.

## 3. The hook

The hook contains the `useForm` call and nothing else — no mutations, no side effects, no derived state. It exists so the generics and the resolver are written once, and so the component reads as markup. Don't park type aliases here either; rule 5 says where those go.

```ts
// ✅
return useForm<InviteMemberFormInput, unknown, InviteMemberFormOutput>({
  defaultValues,
  mode: "onTouched",
  resolver: zodResolver(inviteMemberFormSchema),
});
```

```ts
// ❌ one generic pins input and output to the same type and fights the resolver
return useForm<InviteMemberFormOutput>({
  resolver: zodResolver(inviteMemberFormSchema),
});
```

All three generics are required whenever input and output can differ: `TFieldValues` is what the fields hold, `TContext` is `unknown` when you don't use a resolver context, and `TTransformedValues` is what `handleSubmit` hands you. Getting this right is what makes the parent's `onSubmit` receive a fully parsed `…FormOutput` with no cast.

**`mode: 'onTouched'` is the default for every form**, and only changes if a task explicitly asks for a different mode for one specific form. It validates on first blur and on every change after that, which means a field never turns red before the user has had a go at it, but corrections are reflected immediately. `reValidateMode` stays at its default. If you do deviate, leave a one-line comment saying which requirement made you.

The hook accepts `defaultValues` only when a caller needs to prefill the form — typically an edit form. Otherwise it takes no argument. Add any other option the same way: when a caller needs it, not before.

## 4. Submitting

- The submit handler comes **from the parent as an `onSubmit` prop**, typed `(values: …FormOutput) => void | Promise<void>`. The form component validates and collects; it does not know what the values are for. That's what lets the component be the unit of reuse.
- It is wired on the **form element**: `<form onSubmit={handleSubmit(onSubmit)}>`. Not on the button's `onClick` — that skips Enter-to-submit and breaks keyboard users.
- There is always a `<button type="submit">` inside the form. The explicit `type` matters because a button's default type is `submit` in HTML but `button` in some component libraries, and the ambiguity is not worth carrying.
- Everything after `onSubmit` — the mutation, server rejections, mapping server validation errors onto fields, success feedback — belongs to the caller and is out of scope for this skill. Don't add a `setError('root.serverError')` or a `reset()` on success inside the form component: that ties the form to one caller's API and stops it being reusable.

### The button is not disabled

Never disable the submit button because the form is invalid, untouched, or not dirty.

A disabled submit button is a dead end: the user sees nothing happen, gets no message, and has no way to find out which field is wrong. Keeping it clickable means a click always runs validation and always surfaces the errors — which, with `onTouched`, is exactly how an untouched form tells the user what it needs.

```tsx
// ❌
<button disabled={!isValid} type="submit">Send invite</button>
<button disabled={!isDirty || !isValid} type="submit">Send invite</button>
```

The one exception is a submit already in flight, where blocking a second click prevents a duplicate write. How you express that depends on the button component:

```tsx
// ✅ when the button component has a loading prop, use it
<Button isLoading={isSubmitting} type="submit">Send invite</Button>

// ✅ otherwise, disabled plus a visible pending indicator
<button disabled={isSubmitting} type="submit">
  {isSubmitting ? "Sending…" : "Send invite"}
</button>
```

Read `isSubmitting` from `useFormState({ control })`, per rule 6.

### No `id` on the form element

Leave the `<form>` without an `id` — while every submit button is inside it, the attribute does nothing. The one exception is a submit button that has to live outside the form element (a modal footer, a sticky action bar); for that case, read `references/submit-button-outside-form.md`.

## 5. Fields: inline or extracted

**Keep a field inline in the main component by default.** A form component that shows all its fields in one place is easy to scan, and most fields are a label, an input and an error.

**Extract a field into its own component when any one of these is true:**

- it needs its own `useController`, `useWatch` or `useFormState` subscription
- its behaviour depends on another field's value
- it fetches or derives its own data (async options, a search, a remote lookup)
- it holds local UI state of its own (open/closed, a preview, a cropper)
- its markup plus logic runs past roughly 15 lines

The first three are the ones that really matter: each of them is a re-render boundary. A `useWatch` in the main component re-renders every field on every keystroke; the same `useWatch` inside a child re-renders only that child.

The component lives in the same form folder and is named `<FormName><Field>` — `InviteMemberFormTeamField.tsx`. The form-name prefix is deliberate: it keeps the file unambiguous in search results and in imports, and it signals that this component belongs to one form and is not a shared field widget.

It receives `control` as a prop — never the whole form object, which hands the child more power than it needs and widens the re-render surface. Typing that prop takes a `Control` alias, which depends on `react-hook-form` and so doesn't belong in the schema file: it goes in `<form-name>.types.ts`, created only when a field component imports it.

When you extract a field, read `references/field-component.md` first. It shows how the alias is derived and gives a complete field component to model yours on.

### `register` or `Controller`

- **`register`** when the element accepts a ref and exposes native `value` / `onChange` / `onBlur`: `<input>`, `<select>`, `<textarea>`, and UI components that forward their ref to one. This is the default; it keeps the field uncontrolled and doesn't re-render the form on every keystroke.
- **`Controller` / `useController`** when the component is controlled and doesn't forward a ref, or when the value isn't a plain string, number or boolean — date pickers, multi-selects that return objects, masked or formatted inputs, custom toggles.

Inside an extracted field component, prefer `useController` over rendering a `<Controller>`: you already have a component to put the logic in, so the render-prop layer buys nothing.

## 6. Watching values and reading form state

Destructure what you need from the hook — that part is just naming:

```tsx
// ✅
const { control, handleSubmit, register } = useInviteMemberForm();
```

**But never pull `watch` or `formState` out of `useForm` or `useFormContext`. Use `useWatch` and `useFormState` instead.**

```tsx
// ❌
const {
  formState: { errors, isSubmitting },
  register,
  watch,
} = useInviteMemberForm();
const email = watch("email");
```

```tsx
// ✅
const { control, handleSubmit, register } = useInviteMemberForm();
const { errors, isSubmitting } = useFormState({ control });
const email = useWatch({ control, name: "email" });
```

Those two members are special, for two different reasons.

`formState` is a proxy that arms its subscriptions as a side effect of _reading a property_ — touching `formState.errors` during render is what tells react-hook-form to re-render you when errors change. React Compiler has no way to know that; it sees a plain property read, treats it as pure, and memoizes it. The getter then never runs, the subscription is never armed, and `errors` or `isSubmitting` quietly stop updating. It's a nasty failure because nothing throws — the form just goes stale.

`watch` subscribes the component that called `useForm` to every change in the form, so one watched field re-renders every other field on each keystroke.

`useWatch` and `useFormState` avoid both problems: they subscribe explicitly through `control`, as hooks, so memoization can't disarm them, and each one re-renders only the component that called it.

Two details:

- Destructuring the object returned by `useFormState` is fine and expected — the rule is about `useForm` and `useFormContext`.
- Prefer naming what you need: `useFormState({ control, name: 'email' })` and `useWatch({ control, name: 'email' })` subscribe to one field rather than the whole form.

## 7. FormProvider

**Don't use `FormProvider` by default.** Passing `control` to the handful of components that need it is explicit, type-safe without ceremony, and keeps every field's dependency visible at the call site. Context mainly buys you the ability to stop threading a prop — which is not a problem you have when the tree is one level deep, and is the whole reason the field components live in the same folder.

It is justified only when threading `control` is genuinely impractical:

- fields nested several levels below the form component
- a field subtree composed by the form's consumers (children / slots), so you can't pass props at all
- the project's `Field` component reads the form from context rather than taking `control`

When one of these applies, read `references/form-provider.md` before writing it. It covers where the provider goes and the typed `use…FormContext` hook that every descendant must use instead of calling `useFormContext` directly.

---

## Before you finish

Run through this for every form you created or edited:

- [ ] One folder, PascalCase, holding the component, the hook and the schema
- [ ] Schema file kebab-case + `.schema.ts`; const `…FormSchema`; types `…FormInput` / `…FormOutput` via `z.input` / `z.output`; no `z.infer`
- [ ] `useForm<Input, unknown, Output>` with `zodResolver` and `mode: 'onTouched'`, and nothing else in the hook file
- [ ] The hook takes `defaultValues` only if the form is prefilled; otherwise no argument
- [ ] `onSubmit` is a prop taking `…FormOutput`; wired via `handleSubmit` on the `<form>` element
- [ ] `<button type="submit">` present, not disabled by validity or dirtiness; only an in-flight submit may lock it
- [ ] No `id` on the form element, unless a submit button sits outside it (`references/submit-button-outside-form.md`)
- [ ] Fields built with the project's own components when it has them; plain elements wired with `htmlFor`/`id`, `aria-invalid`, `aria-describedby` and `role="alert"`
- [ ] Extracted fields only where the test in rule 5 says so, named `<FormName><Field>`, taking `control` — built from `references/field-component.md`
- [ ] No `watch` or `formState` destructured from `useForm` / `useFormContext`
- [ ] No `FormProvider` unless rule 7 justifies it — and then following `references/form-provider.md`
- [ ] Lint and typecheck pass on every file you touched, using the commands in the project's `AGENTS.md` if present, or in package.json otherwise
