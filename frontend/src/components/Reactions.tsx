import {
  Group,
  ActionIcon,
  Text,
  Popover,
  SimpleGrid,
  Tooltip,
  UnstyledButton,
  Box,
} from "@mantine/core"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { IconMoodSmile } from "@tabler/icons-react"
import { useState } from "react"

import type { ReactionSummary, ReactionType } from "../types"

// Emoji map for reactions
const REACTION_EMOJIS: Record<ReactionType, string> = {
  like: "\u{1F44D}",
  heart: "\u2764\uFE0F",
  laugh: "\u{1F602}",
  surprised: "\u{1F62E}",
  sad: "\u{1F622}",
  celebrate: "\u{1F389}",
}

const REACTION_LABELS: Record<ReactionType, string> = {
  like: "Synes godt om",
  heart: "Elsker",
  laugh: "Sjovt",
  surprised: "Overrasket",
  sad: "Ked af det",
  celebrate: "Fejrer",
}

interface ReactionsProps {
  reactions: ReactionSummary[]
  toggleFn: (type: ReactionType) => Promise<unknown>
  queryKey: unknown[]
}

export default function Reactions({ reactions, toggleFn, queryKey }: ReactionsProps) {
  const queryClient = useQueryClient()
  const [popoverOpened, setPopoverOpened] = useState(false)

  const toggleMutation = useMutation({
    mutationFn: (reactionType: ReactionType) => toggleFn(reactionType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setPopoverOpened(false)
    },
  })

  const handleReaction = (reactionType: ReactionType) => {
    toggleMutation.mutate(reactionType)
  }

  const allReactionTypes: ReactionType[] = [
    "like",
    "heart",
    "laugh",
    "surprised",
    "sad",
    "celebrate",
  ]

  return (
    <Group gap="sm">
      {/* Display existing reactions */}
      {reactions.map((reaction) => (
        <Tooltip
          key={reaction.reaction_type}
          label={reaction.users.join(", ")}
          multiline
          maw={200}
        >
          <UnstyledButton
            onClick={() => handleReaction(reaction.reaction_type)}
            disabled={
              toggleMutation.isPending &&
              toggleMutation.variables === reaction.reaction_type
            }
          >
            <Box
              px="xs"
              py={4}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--mantine-spacing-xs)",
                borderRadius: "var(--mantine-radius-md)",
                backgroundColor: reaction.has_reacted
                  ? "var(--mantine-color-blue-light)"
                  : "var(--mantine-color-default-hover)",
                border: `1px solid ${
                  reaction.has_reacted
                    ? "var(--mantine-color-blue-light-color)"
                    : "var(--mantine-color-default-border)"
                }`,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <Text size="sm" lh={1}>
                {reaction.emoji}
              </Text>
              <Text
                size="sm"
                fw={600}
                c={reaction.has_reacted ? "blue.7" : "gray.7"}
              >
                {reaction.count}
              </Text>
            </Box>
          </UnstyledButton>
        </Tooltip>
      ))}

      {/* Add reaction button */}
      <Popover
        opened={popoverOpened}
        onChange={setPopoverOpened}
        position="top"
        withArrow
      >
        <Popover.Target>
          <Tooltip label="Tilføj reaktion">
            <ActionIcon
              variant="subtle"
              color="gray"
              size="md"
              onClick={() => setPopoverOpened((o) => !o)}
            >
              <IconMoodSmile size={18} />
            </ActionIcon>
          </Tooltip>
        </Popover.Target>
        <Popover.Dropdown p="xs">
          <SimpleGrid cols={6} spacing="xs">
            {allReactionTypes.map((type) => {
              const existingReaction = reactions.find(
                (r) => r.reaction_type === type,
              )
              return (
                <Tooltip key={type} label={REACTION_LABELS[type]}>
                  <ActionIcon
                    variant={
                      existingReaction?.has_reacted ? "filled" : "subtle"
                    }
                    color={existingReaction?.has_reacted ? "blue" : "gray"}
                    size="xl"
                    onClick={() => handleReaction(type)}
                    loading={
                      toggleMutation.isPending &&
                      toggleMutation.variables === type
                    }
                  >
                    <Text size="xl">{REACTION_EMOJIS[type]}</Text>
                  </ActionIcon>
                </Tooltip>
              )
            })}
          </SimpleGrid>
        </Popover.Dropdown>
      </Popover>
    </Group>
  )
}
