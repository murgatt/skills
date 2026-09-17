import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import type { DefaultValues } from 'react-hook-form';

import { shippingAddressFormSchema } from './shipping-address-form.schema';
import type {
  ShippingAddressFormInput,
  ShippingAddressFormOutput,
} from './shipping-address-form.schema';

type UseShippingAddressFormOptions = {
  defaultValues?: DefaultValues<ShippingAddressFormInput>;
};

export function useShippingAddressForm({
  defaultValues,
}: UseShippingAddressFormOptions = {}) {
  return useForm<ShippingAddressFormInput, unknown, ShippingAddressFormOutput>({
    defaultValues,
    mode: 'onTouched',
    resolver: zodResolver(shippingAddressFormSchema),
  });
}
