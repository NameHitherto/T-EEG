"use client";

import { Database, EllipsisVertical } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar";
import { type DatasetId, datasets, getDatasetById } from "@/data/datasets";
import { persistPreference } from "@/lib/preferences/preferences-storage";
import { cn } from "@/lib/utils";
import { usePreferencesStore } from "@/stores/preferences/preferences-provider";

export function NavDataset() {
  const { isMobile } = useSidebar();
  const activeDataset = usePreferencesStore((s) => s.activeDataset);
  const setActiveDataset = usePreferencesStore((s) => s.setActiveDataset);
  const current = getDatasetById(activeDataset);

  async function handleSelect(id: DatasetId) {
    setActiveDataset(id);
    await persistPreference("active_dataset", id);
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-accent text-sidebar-accent-foreground">
                <Database className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{current.name}</span>
                <span className="truncate text-muted-foreground text-xs">Active dataset</span>
              </div>
              <EllipsisVertical className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-muted-foreground text-xs">Switch dataset</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {datasets.map((dataset) => (
              <DropdownMenuItem
                key={dataset.id}
                className={cn(dataset.id === current.id && "bg-accent/50")}
                aria-current={dataset.id === current.id ? "true" : undefined}
                onClick={() => handleSelect(dataset.id)}
              >
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{dataset.name}</span>
                  <span className="truncate text-muted-foreground text-xs">{dataset.description}</span>
                </div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
