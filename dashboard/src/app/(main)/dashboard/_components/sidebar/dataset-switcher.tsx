"use client";

import { Check, ChevronsUpDown, Database } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { type DatasetId, datasets, getDatasetById } from "@/data/datasets";
import { persistPreference } from "@/lib/preferences/preferences-storage";
import { cn } from "@/lib/utils";
import { usePreferencesStore } from "@/stores/preferences/preferences-provider";

export function DatasetSwitcher() {
  const activeDataset = usePreferencesStore((s) => s.activeDataset);
  const setActiveDataset = usePreferencesStore((s) => s.setActiveDataset);
  const current = getDatasetById(activeDataset);

  async function handleSelect(id: DatasetId) {
    setActiveDataset(id);
    await persistPreference("active_dataset", id);
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-1.5 py-1 text-sm outline-none hover:bg-accent">
        <Database className="size-4 text-muted-foreground" />
        <span className="font-medium">{current.name}</span>
        <ChevronsUpDown className="size-3.5 text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-56 space-y-1 rounded-lg" side="bottom" align="end" sideOffset={4}>
        <DropdownMenuLabel className="text-muted-foreground text-xs">Dataset</DropdownMenuLabel>
        {datasets.map((dataset) => (
          <DropdownMenuItem
            key={dataset.id}
            className={cn("p-0", dataset.id === current.id && "bg-accent/50")}
            aria-current={dataset.id === current.id ? "true" : undefined}
            onClick={() => handleSelect(dataset.id)}
          >
            <div className="flex w-full items-center gap-2 px-1 py-1.5">
              <div className="grid min-w-0 flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{dataset.name}</span>
                <span className="truncate text-muted-foreground text-xs">{dataset.description}</span>
              </div>
              <span
                className={cn(
                  "mr-1 flex size-5 items-center justify-center rounded-full text-primary opacity-0",
                  dataset.id === current.id && "opacity-100",
                )}
              >
                <Check aria-hidden="true" />
              </span>
            </div>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <div className="px-2 py-1.5 text-muted-foreground text-xs">
          API base: <span className="font-mono">/api/{current.apiSegment}</span>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
