# FormProvider, when it is justified

Read this only after rule 7 in `SKILL.md` has told you `FormProvider` is justified: fields nested several levels deep, a field subtree composed by the form's consumers, or a project `Field` component that reads the form from context. In every other case, pass `control` as a prop instead.

Everything else in `SKILL.md` still applies. The only difference is how descendants reach the form.

## The provider lives in the main form component

The main form component is the only place that renders `FormProvider`. It keeps the whole form object rather than destructuring it, because the provider needs all of it spread in:

```tsx
// InviteMemberForm.tsx
import { FormProvider, useFormState } from "react-hook-form";

// …

export function InviteMemberForm({ onSubmit }: InviteMemberFormProps) {
  const form = useInviteMemberForm();
  const { isSubmitting } = useFormState({ control: form.control });

  return (
    <FormProvider {...form}>
      <form noValidate onSubmit={form.handleSubmit(onSubmit)}>
        {/* fields and nested sections */}
        <button disabled={isSubmitting} type="submit">
          Send invite
        </button>
      </form>
    </FormProvider>
  );
}
```

Don't put the provider in a parent page, and don't nest a second one inside the form. One form, one provider, owned by the component that owns the `<form>`.

## A typed context hook for descendants

Create `use<FormName>Context.ts` in the form folder. It is the only place in the codebase that calls `useFormContext` for this form:

```ts
// useInviteMemberFormContext.ts
import { useFormContext } from "react-hook-form";

import type {
  InviteMemberFormInput,
  InviteMemberFormOutput,
} from "./invite-member-form.schema";

export function useInviteMemberFormContext() {
  return useFormContext<
    InviteMemberFormInput,
    unknown,
    InviteMemberFormOutput
  >();
}
```

Every descendant calls `useInviteMemberFormContext()`, never `useFormContext()` directly. The raw hook needs its three generics restated at each call site, and the first one typed loosely — or not at all — silently turns every field name in that component into an unchecked string. One typed hook removes that failure for good.

```tsx
// ❌ untyped, or typed by hand in every file
const { register } = useFormContext();
const { register } = useFormContext<InviteMemberFormInput>();

// ✅
const { register } = useInviteMemberFormContext();
```

A descendant that uses the context hook doesn't need a `control` prop, so it doesn't need the `Control` alias from `invite-member-form.types.ts` either. Only create that types file if some component still takes `control` as a prop.

## Rule 6 still applies inside the context

`useFormContext` returns the same object as `useForm`, with the same `watch` and `formState` hazards. Take `control` from the typed hook and subscribe through `useWatch` / `useFormState`:

```tsx
// ❌
const {
  formState: { errors },
  watch,
} = useInviteMemberFormContext();

// ✅
const { control } = useInviteMemberFormContext();
const { errors } = useFormState({ control, name: "email" });
const role = useWatch({ control, name: "role" });
```

## Checklist

- [ ] One of rule 7's three cases actually applies
- [ ] `FormProvider` rendered once, in the main form component, wrapping the `<form>`
- [ ] `use<FormName>Context.ts` in the form folder, with all three generics
- [ ] No direct `useFormContext()` call anywhere else for this form
- [ ] No `watch` or `formState` destructured from the context hook
