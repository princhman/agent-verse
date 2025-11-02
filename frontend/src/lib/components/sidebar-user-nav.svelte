<script lang="ts">
	import type { User } from '$lib/server/db/schema';
	import ChevronUp from './icons/chevron-up.svelte';
	import {
		DropdownMenu,
		DropdownMenuContent,
		DropdownMenuItem,
		DropdownMenuTrigger
	} from './ui/dropdown-menu';
	import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from './ui/sidebar';
	import { getTheme } from '@sejohnson/svelte-themes';

	let { user }: { user: User } = $props();
	const theme = getTheme();
</script>

<SidebarMenu>
	<SidebarMenuItem>
		<DropdownMenu>
			<DropdownMenuTrigger>
				{#snippet child({ props })}
					<SidebarMenuButton
						{...props}
						class="bg-background data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground h-10"
					>
						<span class="truncate">{user?.email ?? 'Default user'}</span>
						<ChevronUp class="ml-auto" />
					</SidebarMenuButton>
				{/snippet}
			</DropdownMenuTrigger>
			<DropdownMenuContent side="top" class="w-[--bits-floating-anchor-width]">
				<DropdownMenuItem
					class="cursor-pointer"
					onSelect={() =>
						(theme.selectedTheme = theme.resolvedTheme === 'light' ? 'dark' : 'light')}
				>
					Toggle {theme.resolvedTheme === 'light' ? 'dark' : 'light'} mode
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	</SidebarMenuItem>
</SidebarMenu>
