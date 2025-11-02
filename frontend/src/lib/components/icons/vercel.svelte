<script lang="ts">
	let {
		size = 32
	} = $props();
</script>

<img 
	src="/logo.png" 
	alt="Logo" 
	width={size} 
	height={size} 
	style="width: {size}px; height: {size}px; object-fit: contain;"
/>
