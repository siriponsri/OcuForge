import { Box, Flex, HStack, Text } from "@chakra-ui/react";

export function PageHeader({ eyebrow, title, description, children }) {
  return (
    <Flex className="page-header" align={{ base: "flex-start", lg: "flex-end" }} justify="space-between" gap="5" wrap="wrap">
      <Box>
        <Text className="eyebrow">{eyebrow}</Text>
        <Text as="h1" className="page-title">{title}</Text>
        <Text className="page-description">{description}</Text>
      </Box>
      {children && <HStack className="page-actions" gap="2">{children}</HStack>}
    </Flex>
  );
}
