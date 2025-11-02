import { json } from '@sveltejs/kit';
import type { RequestHandler } from '@sveltejs/kit';
import { sync_moodle } from '$lib/server/flask_handler';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const { userId } = await request.json();

		if (!userId) {
			return json({ error: 'userId is required' }, { status: 400 });
		}

		await sync_moodle(userId);

		return json({ success: true });
	} catch (error) {
		console.error('Error in sync-moodle endpoint:', error);
		return json({ error: 'Failed to sync Moodle' }, { status: 500 });
	}
};
