<script setup>
import { isVNode } from 'vue';
import { AlertCircle, CheckCircle2 } from 'lucide-vue-next';
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from '.';
import { useToast } from './use-toast';

const { toasts } = useToast();
</script>

<template>
  <ToastProvider>
    <Toast v-for="toast in toasts" :key="toast.id" v-bind="toast">
      <AlertCircle v-if="toast.variant === 'destructive'" class="h-5 w-5 shrink-0" aria-hidden="true" />
      <CheckCircle2 v-else class="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      <div class="grid min-w-0 flex-1 gap-1">
        <ToastTitle v-if="toast.title">
          {{ toast.title }}
        </ToastTitle>
        <template v-if="toast.description">
          <ToastDescription v-if="isVNode(toast.description)">
            <component :is="toast.description" />
          </ToastDescription>
          <ToastDescription v-else>
            {{ toast.description }}
          </ToastDescription>
        </template>
        <ToastClose />
      </div>
      <component :is="toast.action" />
    </Toast>
    <ToastViewport />
  </ToastProvider>
</template>
