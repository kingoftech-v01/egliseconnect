'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useResetPassword } from '@/hooks/use-auth';
import { ApiClientError } from '@egliseconnect/api-client';

const schema = z
  .object({
    new_password: z.string().min(8, 'Minimum 8 caractères'),
    new_password_confirm: z.string(),
  })
  .refine((d) => d.new_password === d.new_password_confirm, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['new_password_confirm'],
  });

type FormData = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const uid = searchParams.get('uid') || '';
  const token = searchParams.get('token') || '';

  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState(false);
  const { mutate: resetPassword, isPending } = useResetPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  if (!uid || !token) {
    return (
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Lien invalide</CardTitle>
          <CardDescription>
            Ce lien de réinitialisation est invalide ou a expiré.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Link href="/forgot-password" className="text-sm text-primary hover:underline">
            Demander un nouveau lien
          </Link>
        </CardFooter>
      </Card>
    );
  }

  function onSubmit(data: FormData) {
    setServerError('');
    resetPassword(
      { uid, token, ...data },
      {
        onSuccess: () => setSuccess(true),
        onError: (error) => {
          if (error instanceof ApiClientError) {
            setServerError(error.message);
          } else {
            setServerError('Une erreur est survenue. Veuillez réessayer.');
          }
        },
      },
    );
  }

  if (success) {
    return (
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Mot de passe réinitialisé</CardTitle>
          <CardDescription>
            Votre mot de passe a été modifié avec succès.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Link href="/login" className="text-sm text-primary hover:underline">
            Se connecter
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Nouveau mot de passe</CardTitle>
        <CardDescription>Choisissez un nouveau mot de passe pour votre compte.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {serverError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {serverError}
            </div>
          )}
          <div className="space-y-2">
            <label htmlFor="new_password" className="text-sm font-medium">
              Nouveau mot de passe
            </label>
            <Input
              id="new_password"
              type="password"
              placeholder="Minimum 8 caractères"
              {...register('new_password')}
            />
            {errors.new_password && (
              <p className="text-xs text-destructive">{errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <label htmlFor="new_password_confirm" className="text-sm font-medium">
              Confirmer le mot de passe
            </label>
            <Input
              id="new_password_confirm"
              type="password"
              placeholder="Confirmez le mot de passe"
              {...register('new_password_confirm')}
            />
            {errors.new_password_confirm && (
              <p className="text-xs text-destructive">{errors.new_password_confirm.message}</p>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? 'Réinitialisation...' : 'Réinitialiser le mot de passe'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
