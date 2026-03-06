'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useLogin } from '@/hooks/use-auth';
import { ApiClientError } from '@egliseconnect/api-client';

const loginSchema = z.object({
  email: z.string().email('Adresse courriel invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [serverError, setServerError] = useState('');
  const { mutate: login, isPending } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  function onSubmit(data: LoginFormData) {
    setServerError('');
    login(data, {
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
        <CardTitle className="text-2xl">ÉgliseConnect</CardTitle>
        <CardDescription>Connectez-vous à votre compte</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {serverError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {serverError}
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Courriel
            </label>
            <Input
              id="email"
              type="email"
              placeholder="votre@courriel.com"
              {...register('email')}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Mot de passe
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Votre mot de passe"
              {...register('password')}
            />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>
        </CardContent>

        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? 'Connexion...' : 'Se connecter'}
          </Button>
          <Link href="/forgot-password" className="text-sm text-muted-foreground hover:underline">
            Mot de passe oublié?
          </Link>
          <p className="text-sm text-muted-foreground">
            Pas encore de compte?{' '}
            <Link href="/signup" className="text-primary hover:underline">
              S&apos;inscrire
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
