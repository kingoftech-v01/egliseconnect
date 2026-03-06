'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateMember } from '@/hooks/use-members';

const memberSchema = z.object({
  first_name: z.string().min(1, 'Prénom requis'),
  last_name: z.string().min(1, 'Nom requis'),
  email: z.string().email('Courriel invalide'),
  phone: z.string().optional(),
  birth_date: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  province: z.string().optional(),
  postal_code: z.string().optional(),
});

type MemberFormData = z.infer<typeof memberSchema>;

export default function NewMemberPage() {
  const router = useRouter();
  const { mutate: createMember, isPending } = useCreateMember();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<MemberFormData>({
    resolver: zodResolver(memberSchema),
  });

  function onSubmit(data: MemberFormData) {
    createMember(data, {
      onSuccess: () => router.push('/members'),
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/members">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">Nouveau membre</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Informations personnelles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Prénom *</label>
                <Input {...register('first_name')} />
                {!!errors.first_name && (
                  <p className="text-xs text-destructive">{errors.first_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Nom *</label>
                <Input {...register('last_name')} />
                {!!errors.last_name && (
                  <p className="text-xs text-destructive">{errors.last_name.message}</p>
                )}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Courriel *</label>
                <Input type="email" {...register('email')} />
                {!!errors.email && (
                  <p className="text-xs text-destructive">{errors.email.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Téléphone</label>
                <Input type="tel" {...register('phone')} />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Date de naissance</label>
              <Input type="date" {...register('birth_date')} />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Adresse</label>
              <Input {...register('address')} />
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Ville</label>
                <Input {...register('city')} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Province</label>
                <Input {...register('province')} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Code postal</label>
                <Input {...register('postal_code')} />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Création...' : 'Créer le membre'}
              </Button>
              <Link href="/members">
                <Button type="button" variant="outline">
                  Annuler
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
