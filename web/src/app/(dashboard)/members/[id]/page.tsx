'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft, Edit, Phone, Mail, MapPin, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { useMember } from '@/hooks/use-members';
import { ROLE_LABELS, MEMBERSHIP_STATUS_LABELS } from '@egliseconnect/types';
import { formatDate, formatPhoneNumber } from '@egliseconnect/utils';

export default function MemberDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: member, isLoading } = useMember(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!member) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Membre introuvable</p>
        <Link href="/members" className="text-primary hover:underline mt-2 inline-block">
          Retour à la liste
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/members">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{member.full_name}</h1>
          <p className="text-muted-foreground">{member.member_number}</p>
        </div>
        <Link href={`/members/${id}/edit`}>
          <Button variant="outline">
            <Edit className="h-4 w-4 mr-2" />
            Modifier
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardContent className="pt-6 text-center">
            <Avatar
              src={member.photo}
              fallback={member.full_name}
              size="lg"
              className="mx-auto h-24 w-24 text-2xl"
            />
            <h2 className="mt-4 text-lg font-semibold">{member.full_name}</h2>
            <div className="mt-2 flex justify-center gap-2">
              <Badge variant="outline">
                {ROLE_LABELS[member.role as keyof typeof ROLE_LABELS] || member.role}
              </Badge>
              <Badge variant={member.membership_status === 'active' ? 'success' : 'secondary'}>
                {MEMBERSHIP_STATUS_LABELS[member.membership_status as keyof typeof MEMBERSHIP_STATUS_LABELS] || member.membership_status}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Informations</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <InfoItem icon={Mail} label="Courriel" value={member.email} />
            <InfoItem icon={Phone} label="Téléphone" value={member.phone ? formatPhoneNumber(member.phone) : '—'} />
            <InfoItem
              icon={MapPin}
              label="Adresse"
              value={
                [member.address, member.city, member.province, member.postal_code]
                  .filter(Boolean)
                  .join(', ') || '—'
              }
            />
            <InfoItem icon={Calendar} label="Date de naissance" value={member.birth_date ? formatDate(member.birth_date) : '—'} />
            <InfoItem icon={Calendar} label="Membre depuis" value={member.joined_date ? formatDate(member.joined_date) : '—'} />
            <InfoItem icon={Calendar} label="Baptême" value={member.baptism_date ? formatDate(member.baptism_date) : '—'} />
          </CardContent>
        </Card>
      </div>

      {member.groups && member.groups.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Groupes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {member.groups.map((g) => (
                <Badge key={g.id} variant="outline">
                  {g.group_name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm">{value}</p>
      </div>
    </div>
  );
}
