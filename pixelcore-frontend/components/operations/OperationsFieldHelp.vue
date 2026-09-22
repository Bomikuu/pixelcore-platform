<template>
  <TooltipProvider :delay-duration="250">
    <Tooltip>
      <TooltipTrigger as-child>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          class="h-6 w-6 shrink-0 text-muted-foreground hover:text-foreground"
          :aria-label="label"
        >
          <CircleHelp class="h-4 w-4" aria-hidden="true" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" class="max-w-xs text-balance leading-5">
        {{ text }}
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
</template>

<script setup>
import { CircleHelp } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

defineProps({
  text: { type: String, required: true },
  label: { type: String, default: 'Explain this field' },
})
</script>
