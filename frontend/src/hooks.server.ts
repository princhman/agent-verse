import { sequence } from '@sveltejs/kit/hooks';
import { handle as authHandle } from '$lib/server/auth';

export const handle = sequence(authHandle);
