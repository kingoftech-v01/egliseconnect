/** Client-side permission checking utilities. */
import {
  type Role,
  ROLE_HIERARCHY,
  STAFF_ROLES,
  FINANCE_ROLES,
  LEADERSHIP_ROLES,
} from '@egliseconnect/types';

export function hasRole(userRoles: Role[], requiredRole: Role): boolean {
  const requiredLevel = ROLE_HIERARCHY.indexOf(requiredRole);
  return userRoles.some((role) => ROLE_HIERARCHY.indexOf(role) >= requiredLevel);
}

export function hasAnyRole(userRoles: Role[], requiredRoles: Role[]): boolean {
  return userRoles.some((role) => requiredRoles.includes(role));
}

export function isStaff(userRoles: Role[]): boolean {
  return hasAnyRole(userRoles, STAFF_ROLES);
}

export function canAccessFinance(userRoles: Role[]): boolean {
  return hasAnyRole(userRoles, FINANCE_ROLES);
}

export function isLeadership(userRoles: Role[]): boolean {
  return hasAnyRole(userRoles, LEADERSHIP_ROLES);
}
