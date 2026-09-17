import { useEffect } from 'react';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

export const profileSchema = z.object({
  displayName: z.string().min(2, 'Too short'),
  email: z.string().email('Invalid email'),
  bio: z.string().max(280).optional(),
  newsletter: z.boolean().default(false),
});

export type ProfileValues = z.infer<typeof profileSchema>;

export function ProfileSettingsForm() {
  const methods = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    mode: 'onChange',
  });

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid, isDirty, isSubmitting },
  } = methods;

  const newsletter = watch('newsletter');

  useEffect(() => {
    if (newsletter) {
      console.log('subscribed');
    }
  }, [newsletter]);

  async function save(values: ProfileValues) {
    await fetch('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(values),
    });
  }

  return (
    <FormProvider {...methods}>
      <div>
        <input {...register('displayName')} />
        {errors.displayName && <span>{errors.displayName.message}</span>}

        <input {...register('email')} />
        {errors.email && <span>{errors.email.message}</span>}

        <textarea {...register('bio')} />

        <label>
          <input type="checkbox" {...register('newsletter')} />
          Send me the newsletter
        </label>

        <button onClick={handleSubmit(save)} disabled={!isValid || !isDirty || isSubmitting}>
          Save
        </button>
      </div>
    </FormProvider>
  );
}
