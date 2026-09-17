# A submit button outside the form

Read this only when a submit button can't live inside the `<form>` element — a modal footer, a sticky action bar, a page header. In every other case the form has no `id` and the button sits inside it (rule 4 in `SKILL.md`).

## Use the HTML `form` attribute

Give the form an `id` and point the button at it with the `form` attribute. That is what the attribute exists for, and it keeps the native submit behaviour: Enter still submits, `handleSubmit` still runs validation, and the button still triggers it like any other submit button.

```tsx
<form id="invite-member-form" noValidate onSubmit={handleSubmit(onSubmit)}>
  {/* fields */}
</form>

<ModalFooter>
  <button form="invite-member-form" type="submit">
    Send invite
  </button>
</ModalFooter>
```

```tsx
// ❌ don't reach into the form with a ref, or lift handleSubmit into the parent
<button onClick={() => formRef.current?.requestSubmit()}>Send invite</button>
<button onClick={handleSubmit(onSubmit)}>Send invite</button>
```

## Naming the id

Hard-code the id as the form's name in kebab-case — the same stem as the schema file: `InviteMemberForm` → `invite-member-form`. The button usually lives in a different component from the form, so the id has to be a known string that both sides can use.

Every other rule still applies to the outside button: `type="submit"`, and never disabled by validity or dirtiness — only an in-flight submit may lock it.
