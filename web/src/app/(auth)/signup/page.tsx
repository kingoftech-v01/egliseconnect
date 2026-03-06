'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useRegister } from '@/hooks/use-auth';
import { ApiClientError } from '@egliseconnect/api-client';

const signupSchema = z
  .object({
    first_name: z.string().min(1, 'Prénom requis'),
    last_name: z.string().min(1, 'Nom requis'),
    email: z.string().email('Adresse courriel invalide'),
    password: z.string().min(8, 'Au moins 8 caractères'),
    password_confirm: z.string(),
    invitation_code: z.string().optional(),
  })
  .refine((data) => data.password === data.password_confirm, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['password_confirm'],
  });

type SignupFormData = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const [serverError, setServerError] = useState('');
  const { mutate: signup, isPending } = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  });

  function onSubmit(data: SignupFormData) {
    setServerError('');
    signup(data, {
      onError: (error) => {
        if (error instanceof ApiClientError) {
          setServerError(error.message);
        } else {
          setServerError('Une erreur est survenue. Veuillez réessayer.');
        }
      },
    });
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Créer un compte</CardTitle>
        <CardDescription>Rejoignez votre communauté</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {serverError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {serverError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="first_name" className="text-sm font-medium">
                Prénom
              </label>
              <Input id="first_name" {...register('first_name')} />
              {errors.first_name && (
                <p className="text-xs text-destructive">{errors.first_name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <label htmlFor="last_name" className="text-sm font-medium">
                Nom
              </label>
              <Input id="last_name" {...register('last_name')} />
              {errors.last_name && (
                <p className="text-xs text-destructive">{errors.last_name.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Courriel
            </label>
            <Input id="email" type="email" {...register('email')} />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Mot de passe
            </label>
            <Input id="password" type="password" {...register('password')} />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="password_confirm" className="text-sm font-medium">
              Confirmer le mot de passe
            </label>
            <Input id="password_confirm" type="password" {...register('password_confirm')} />
            {errors.password_confirm && (
              <p className="text-xs text-destructive">{errors.password_confirm.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="invitation_code" className="text-sm font-medium">
              Code d&apos;invitation (optionnel)
            </label>
            <Input id="invitation_code" {...register('invitation_code')} placeholder="XXXX-XXXX" />
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? 'Création...' : 'Créer mon compte'}
          </Button>
          <p className="text-sm text-muted-foreground">
            Déjà un compte?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Se connecter
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
