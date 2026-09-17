import { z } from 'zod';

export const shippingAddressFormSchema = z.object({
  fullName: z.string().trim().min(1, 'Enter a name'),
  line1: z.string().trim().min(1, 'Enter a street address'),
  city: z.string().trim().min(1, 'Enter a city'),
  postalCode: z.string().trim().min(1, 'Enter a postal code'),
});

export type ShippingAddressFormInput = z.input<typeof shippingAddressFormSchema>;
export type ShippingAddressFormOutput = z.output<typeof shippingAddressFormSchema>;
