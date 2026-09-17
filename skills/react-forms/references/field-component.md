# Extracting a field component

Read this once rule 5 in `SKILL.md` has told you a field earns its own component. The rules there still decide *whether* to extract; this file shows *how*.

The running example: the invite form gains a `teamId` field that only applies to members. It depends on another field (`role`), fetches its own data and needs its own subscriptions — three extraction triggers at once.

## 1. The `Control` alias, in the types file

The field component takes `control` as a prop, and that prop needs a type. Declare it once in `<form-name>.types.ts`, next to the schema — not in the hook file, and not in the schema file, which stays pure zod:

```ts
// invite-member-form.types.ts
import type { UseFormReturn } from 'react-hook-form';

import type {
  InviteMemberFormInput,
  InviteMemberFormOutput,
} from './invite-member-form.schema';

export type InviteMemberFormControl = UseFormReturn<
  InviteMemberFormInput,
  unknown,
  InviteMemberFormOutput
>['control'];
```

Deriving the alias from `UseFormReturn[…]['control']` rather than writing `Control<Input, unknown, Output>` by hand means the three generics are stated once, in the one place that already has to state them.

Create this file only when a field component imports from it. A form with no extracted fields has no types file.

## 2. The field component

It lives in the form folder, is named `<FormName><Field>.tsx`, takes only `control`, and does its own subscribing:

```tsx
// InviteMemberFormTeamField.tsx
import { useController, useWatch } from 'react-hook-form';

import { useTeams } from '@/hooks/useTeams';
import type { InviteMemberFormControl } from './invite-member-form.types';

type InviteMemberFormTeamFieldProps = {
  control: InviteMemberFormControl;
};

export function InviteMemberFormTeamField({
  control,
}: InviteMemberFormTeamFieldProps) {
  const role = useWatch({ control, name: 'role' });
  const { field, fieldState } = useController({ control, name: 'teamId' });
  const { data: teams = [] } = useTeams({ enabled: role === 'member' });

  if (role !== 'member') return null;

  return (
    <div>
      <label htmlFor="invite-member-team">Team</label>
      <TeamSelect
        aria-describedby={
          fieldState.error ? 'invite-member-team-error' : undefined
        }
        aria-invalid={fieldState.invalid}
        id="invite-member-team"
        options={teams}
        {...field}
      />
      {fieldState.error && (
        <p id="invite-member-team-error" role="alert">
          {fieldState.error.message}
        </p>
      )}
    </div>
  );
}
```

What to copy from it:

- **`useWatch` for the field it depends on**, inside the child. The parent never watches `role`, so typing in other fields doesn't re-render this one, and changing `role` re-renders only this one.
- **`useController` rather than a `<Controller>`** — the component already exists to hold the logic, so the render-prop layer adds nothing. Use `register` instead if the input accepts a ref (see rule 5's `register` or `Controller`).
- **Every hook before the early `return null`**, so hiding the field never changes the hook order.
- **Errors from `fieldState`**, which is already scoped to this field — no `useFormState` needed for them.

## 3. Wiring it into the main form

The main component renders it inline among the other fields and passes `control` from the destructured hook:

```tsx
const { control, handleSubmit, register } = useInviteMemberForm();

// …
<InviteMemberFormTeamField control={control} />
```

```tsx
// ❌ don't pass the whole form object — it hands the child more power than it
//    needs and widens the re-render surface
<InviteMemberFormTeamField form={form} />
```

## Checklist

- [ ] One of rule 5's extraction triggers actually applies
- [ ] File named `<FormName><Field>.tsx`, in the form folder
- [ ] Takes `control` only, typed with the alias from `<form-name>.types.ts`
- [ ] Watches the fields it depends on itself, with `useWatch`
- [ ] All hooks run before any early return
