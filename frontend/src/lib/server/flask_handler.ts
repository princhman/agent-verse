import { VITE_FLASK_BACKEND_URL } from '$env/static/private';
import { user } from './db/schema';
import { eq } from 'drizzle-orm';
import postgres from 'postgres';
import { drizzle } from 'drizzle-orm/postgres-js';
import { POSTGRES_URL } from '$env/static/private';

// biome-ignore lint: Forbidden non-null assertion.
const client = postgres(POSTGRES_URL);
const database = drizzle(client);

export async function sync_moodle(userId: string): Promise<void> {
	try {
		const response = await fetch(`${VITE_FLASK_BACKEND_URL}/scrape`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ user_id: userId })
		});

		const data = await response.json();

		if (data.status === 'success') {
			await database.update(user).set({ last_moodle_sync: new Date() }).where(eq(user.id, userId));
		} else {
			console.error('Flask scrape failed:', data);
		}
	} catch (error) {
		console.error('Error calling Flask backend:', error);
	}
}
