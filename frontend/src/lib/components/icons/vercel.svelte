<script lang="ts">
	let {
		size = 80
	} = $props();
</script>

<img 
	src="/logo.png" 
	alt="Logo" 
	width={size} 
	height={size} 
	style="width: {size}px; height: {size}px; object-fit: contain;"
/>
