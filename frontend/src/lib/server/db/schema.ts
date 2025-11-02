import type { InferSelectModel } from 'drizzle-orm';
import {
	pgTable,
	varchar,
	timestamp,
	json,
	uuid,
	text,
	primaryKey,
	foreignKey,
	boolean,
	uniqueIndex
} from 'drizzle-orm/pg-core';

export const user = pgTable('User', {
	id: uuid('id').primaryKey().notNull().defaultRandom().primaryKey(),
	email: varchar('email', { length: 64 }).notNull().unique(),
	password: varchar('password', { length: 64 }).notNull()
});

export type AuthUser = InferSelectModel<typeof user>;
export type User = Omit<AuthUser, 'password'>;

export const session = pgTable('Session', {
	id: text('id').primaryKey().notNull(),
	userId: uuid('userId')
		.notNull()
		.references(() => user.id),
	expiresAt: timestamp('expires_at', {
		withTimezone: true,
		mode: 'date'
	}).notNull()
});

export type Session = InferSelectModel<typeof session>;

export const chat = pgTable('Chat', {
	id: uuid('id').primaryKey().notNull().defaultRandom().primaryKey(),
	createdAt: timestamp('createdAt').notNull(),
	title: text('title').notNull(),
	userId: uuid('userId')
		.notNull()
		.references(() => user.id),
	visibility: varchar('visibility', { enum: ['public', 'private'] })
		.notNull()
		.default('private')
});

export type Chat = InferSelectModel<typeof chat>;

export const message = pgTable('Message', {
	id: uuid('id').primaryKey().notNull().defaultRandom(),
	chatId: uuid('chatId')
		.notNull()
		.references(() => chat.id),
	role: varchar('role').notNull(),
	parts: json('parts').notNull(),
	attachments: json('attachments').notNull(),
	createdAt: timestamp('createdAt').notNull()
});

export type Message = InferSelectModel<typeof message>;

export const vote = pgTable(
	'Vote',
	{
		chatId: uuid('chatId')
			.notNull()
			.references(() => chat.id),
		messageId: uuid('messageId')
			.notNull()
			.references(() => message.id),
		isUpvoted: boolean('isUpvoted').notNull()
	},
	(table) => [
		{
			pk: primaryKey({ columns: [table.chatId, table.messageId] })
		}
	]
);

export type Vote = InferSelectModel<typeof vote>;

export const document = pgTable(
	'Document',
	{
		id: uuid('id').notNull().defaultRandom(),
		createdAt: timestamp('createdAt').notNull(),
		title: text('title').notNull(),
		content: text('content'),
		kind: varchar('text', { enum: ['text', 'code', 'image', 'sheet'] })
			.notNull()
			.default('text'),
		userId: uuid('userId')
			.notNull()
			.references(() => user.id)
	},
	(table) => [
		{
			pk: primaryKey({ columns: [table.id, table.createdAt] })
		}
	]
);

export type Document = InferSelectModel<typeof document>;

export const suggestion = pgTable(
	'Suggestion',
	{
		id: uuid('id').notNull().defaultRandom(),
		documentId: uuid('documentId').notNull(),
		documentCreatedAt: timestamp('documentCreatedAt').notNull(),
		originalText: text('originalText').notNull(),
		suggestedText: text('suggestedText').notNull(),
		description: text('description'),
		isResolved: boolean('isResolved').notNull().default(false),
		userId: uuid('userId')
			.notNull()
			.references(() => user.id),
		createdAt: timestamp('createdAt').notNull()
	},
	(table) => [
		{
			pk: primaryKey({ columns: [table.id] }),
			documentRef: foreignKey({
				columns: [table.documentId, table.documentCreatedAt],
				foreignColumns: [document.id, document.createdAt]
			})
		}
	]
);

export type Suggestion = InferSelectModel<typeof suggestion>;

// Course, Section, and File tables
export const course = pgTable(
	'Course',
	{
		userId: varchar('userId', { length: 255 }).notNull(),
		courseId: varchar('courseId', { length: 255 }).primaryKey().notNull(),
		courseName: varchar('courseName', { length: 255 }).notNull()
	},
	(table) => [
		{
			uniqueCourseId: uniqueIndex('uq_course_id').on(table.courseId)
		}
	]
);

export type Course = InferSelectModel<typeof course>;

export const section = pgTable(
	'Section',
	{
		sectionId: varchar('sectionId', { length: 255 }).primaryKey().notNull(),
		courseId: varchar('courseId', { length: 255 })
			.notNull()
			.references(() => course.courseId),
		content: text('content'),
		title: varchar('title', { length: 255 }),
		createdAt: timestamp('createdAt', {
			withTimezone: true,
			mode: 'date'
		})
			.notNull()
			.defaultNow()
	},
	(table) => [
		{
			courseIdIdx: foreignKey({
				columns: [table.courseId],
				foreignColumns: [course.courseId]
			})
		}
	]
);

export type Section = InferSelectModel<typeof section>;

export const file = pgTable(
	'File',
	{
		path: varchar('path', { length: 500 }).primaryKey().notNull(),
		key: varchar('key', { length: 255 }).notNull().unique(),
		sectionId: varchar('sectionId', { length: 255 }).references(() => section.sectionId),
		courseId: varchar('courseId', { length: 255 })
			.notNull()
			.references(() => course.courseId),
		createdAt: timestamp('createdAt', {
			withTimezone: true,
			mode: 'date'
		})
			.notNull()
			.defaultNow()
	},
	(table) => [
		{
			courseIdIdx: foreignKey({
				columns: [table.courseId],
				foreignColumns: [course.courseId]
			}),
			sectionIdIdx: foreignKey({
				columns: [table.sectionId],
				foreignColumns: [section.sectionId]
			})
		}
	]
);

export type File = InferSelectModel<typeof file>;
