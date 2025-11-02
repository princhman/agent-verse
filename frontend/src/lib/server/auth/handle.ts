import type { Handle } from '@sveltejs/kit';
import type { User, Session } from '../db/schema';

const defaultUser: User = {
	id: 'default-user-id',
	email: 'user@example.com'
};

const defaultSession: Session = {
	id: 'default-session-id',
	userId: defaultUser.id,
	expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 365) // 1 year
};

export const handle: Handle = async ({ event, resolve }) => {
	event.locals.user = defaultUser;
	event.locals.session = defaultSession;
	return resolve(event);
};
