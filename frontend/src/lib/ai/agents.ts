import { Experimental_Agent as Agent, stepCountIs, tool } from 'ai';
import { z } from 'zod';

async function getUCLToken(userId: string): Promise<string> {
	try {
		const response = await fetch('/api/user-token', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_id: userId })
		});
		
		if (!response.ok) {
			throw new Error('Failed to retrieve UCL API token');
		}
		
		const data = await response.json();
		if (!data.token) {
			throw new Error('No UCL API token found. Please login first.');
		}
		return data.token;
	} catch (error) {
		throw new Error(`Failed to retrieve UCL API token: ${error instanceof Error ? error.message : String(error)}`);
	}
}

function getUserId(): string {
	const userId = localStorage.getItem('user_id');
	if (!userId) {
		throw new Error('User ID not found. Please login first.');
	}
	return userId;
}

export const uclapiAgent = new Agent({
	model: undefined as any, // Will be set dynamically from server
	tools: {
		getTimetable: tool({
			description: 'Get the personal timetable for a specific date',
			inputSchema: z.object({
				date: z
					.string()
					.optional()
					.describe('The date in YYYY-MM-DD format (optional, defaults to all dates)')
			}),
			execute: async ({ date }: any) => {
				try {
					const userId = getUserId();
					const ucl_api_token = await getUCLToken(userId);
					const response = await fetch('/api/timetable', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({
							ucl_api_token,
							date: date || ''
						})
					});

					if (!response.ok) {
						const error = await response.json();
						return { error: `Failed to get timetable: ${error.error || response.statusText}` };
					}

					const data = await response.json();
					return data;
				} catch (error) {
					return {
						error: `Failed to get timetable: ${error instanceof Error ? error.message : String(error)}`
					};
				}
			}
		}),
		getFreeRooms: tool({
			description: 'Get a list of all free study spaces at UCL between a start and end time',
			inputSchema: z.object({
				start_datetime: z
					.string()
					.describe('Start date and time in ISO-8601 format (e.g., 2025-11-07T00:00:00Z)'),
				end_datetime: z
					.string()
					.describe('End date and time in ISO-8601 format (e.g., 2025-11-09T00:00:00Z)')
			}),
			execute: async ({ start_datetime, end_datetime }: any) => {
				try {
					const userId = getUserId();
					const ucl_api_token = await getUCLToken(userId);
					const response = await fetch('/api/free-rooms', {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({
							start_datetime,
							end_datetime,
							ucl_api_token
						})
					});

					if (!response.ok) {
						const error = await response.json();
						return { error: `Failed to get free rooms: ${error.error || response.statusText}` };
					}

					const data = await response.json();
					return data;
				} catch (error) {
					return {
						error: `Failed to get free rooms: ${error instanceof Error ? error.message : String(error)}`
					};
				}
			}
		})
	},
	stopWhen: stepCountIs(20)
});

export default uclapiAgent;
