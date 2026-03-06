'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useForgotPassword } from '@/hooks/use-auth';
import { ApiClientError } from '@egliseconnect/api-client';

const schema = z.object({
  email: z.string().email('Adresse courriel invalide'),
});

type FormData = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState(false);
  const { mutate: forgotPassword, isPending } = useForgotPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  function onSubmit(data: FormData) {
    setServerError('');
    forgotPassword(data, {
      onSuccess: () => setSuccess(true),
      onError: (error) => {
        if (error instanceof ApiClientError) {
          setServerError(error.message);
        } else {
          setServerError('Une erreur est survenue. Veuillez réessayer.');
        }
      },
    });
  }

  if (success) {
    return (
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Courriel envoyé</CardTitle>
          <CardDescription>
            Si un compte existe avec cette adresse, un lien de réinitialisation a été envoyé.
            Vérifiez votre boîte de réception.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-center">
          <Link href="/login" className="text-sm text-primary hover:underline">
            Retour à la connexion
          </Link>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Mot de passe oublié</CardTitle>
        <CardDescription>
          Entrez votre adresse courriel pour recevoir un lien de réinitialisation.
        </CardDescription>
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
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? 'Envoi...' : 'Envoyer le lien'}
          </Button>
          <Link href="/login" className="text-sm text-muted-foreground hover:underline">
            Retour à la connexion
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}
