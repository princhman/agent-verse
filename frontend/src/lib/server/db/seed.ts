import { config } from 'dotenv';
import { genSaltSync, hashSync } from 'bcrypt-ts';
import { drizzle } from 'drizzle-orm/postgres-js';
import { eq } from 'drizzle-orm';
import postgres from 'postgres';
import { user } from './schema.ts';

config({
	path: '.env.local'
});

const runSeed = async () => {
	if (!process.env.POSTGRES_URL) {
		throw new Error('POSTGRES_URL is not defined');
	}

	const connection = postgres(process.env.POSTGRES_URL, { max: 1 });
	const db = drizzle(connection);

	console.log('⏳ Seeding database...');

	try {
		// Check if default user already exists
		const existingUser = await db
			.select()
			.from(user)
			.where(eq(user.email, 'default@example.com'))
			.limit(1);

		if (existingUser.length === 0) {
			const salt = genSaltSync(10);
			const hashedPassword = hashSync('default-password-123', salt);

			await db.insert(user).values({
				email: 'default@example.com',
				password: hashedPassword
			});

			console.log('✅ Default user created with email: default@example.com');
		} else {
			console.log('✅ Default user already exists');
		}
	} catch (error) {
		console.error('❌ Seed failed');
		console.error(error);
		process.exit(1);
	} finally {
		await connection.end();
		process.exit(0);
	}
};

runSeed();
