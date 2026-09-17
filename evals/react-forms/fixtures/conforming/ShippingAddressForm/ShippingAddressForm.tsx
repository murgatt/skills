import { useFormState } from 'react-hook-form';
import type { DefaultValues } from 'react-hook-form';

import { useShippingAddressForm } from './useShippingAddressForm';
import type {
  ShippingAddressFormInput,
  ShippingAddressFormOutput,
} from './shipping-address-form.schema';

type ShippingAddressFormProps = {
  defaultValues?: DefaultValues<ShippingAddressFormInput>;
  onSubmit: (values: ShippingAddressFormOutput) => void | Promise<void>;
};

export function ShippingAddressForm({
  defaultValues,
  onSubmit,
}: ShippingAddressFormProps) {
  const { control, handleSubmit, register } = useShippingAddressForm({
    defaultValues,
  });
  const { errors, isSubmitting } = useFormState({ control });

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <label htmlFor="shipping-full-name">Full name</label>
      <input
        aria-describedby={errors.fullName ? 'shipping-full-name-error' : undefined}
        aria-invalid={!!errors.fullName}
        id="shipping-full-name"
        {...register('fullName')}
      />
      {errors.fullName && (
        <p id="shipping-full-name-error" role="alert">
          {errors.fullName.message}
        </p>
      )}

      <label htmlFor="shipping-line1">Address</label>
      <input
        aria-describedby={errors.line1 ? 'shipping-line1-error' : undefined}
        aria-invalid={!!errors.line1}
        id="shipping-line1"
        {...register('line1')}
      />
      {errors.line1 && (
        <p id="shipping-line1-error" role="alert">
          {errors.line1.message}
        </p>
      )}

      <label htmlFor="shipping-city">City</label>
      <input
        aria-describedby={errors.city ? 'shipping-city-error' : undefined}
        aria-invalid={!!errors.city}
        id="shipping-city"
        {...register('city')}
      />
      {errors.city && (
        <p id="shipping-city-error" role="alert">
          {errors.city.message}
        </p>
      )}

      <label htmlFor="shipping-postal-code">Postal code</label>
      <input
        aria-describedby={
          errors.postalCode ? 'shipping-postal-code-error' : undefined
        }
        aria-invalid={!!errors.postalCode}
        id="shipping-postal-code"
        {...register('postalCode')}
      />
      {errors.postalCode && (
        <p id="shipping-postal-code-error" role="alert">
          {errors.postalCode.message}
        </p>
      )}

      <button disabled={isSubmitting} type="submit">
        {isSubmitting ? 'Saving…' : 'Save address'}
      </button>
    </form>
  );
}
