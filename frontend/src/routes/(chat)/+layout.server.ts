import { getDefaultUser } from '$lib/server/db/queries';

export async function load({ cookies }) {
	const sidebarCollapsed = cookies.get('sidebar:state') !== 'true';

	const userResult = await getDefaultUser();
	const user = userResult._unsafeUnwrap();

	return {
		sidebarCollapsed,
		user
	};
}
