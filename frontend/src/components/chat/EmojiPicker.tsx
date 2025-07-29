import React from 'react';
import { Smile } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import data from '@emoji-mart/data';
import Picker from '@emoji-mart/react';
import { cn } from '@/lib/utils';

interface EmojiPickerProps {
  onSelect: (emoji: string) => void;
  children?: React.ReactNode;
  className?: string;
}

export const EmojiPicker: React.FC<EmojiPickerProps> = ({
  onSelect,
  children,
  className,
}) => {
  const handleEmojiSelect = (emojiData: any) => {
    onSelect(emojiData.native);
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        {children || (
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-8 w-8 p-0 text-muted-foreground hover:text-foreground", className)}
          >
            <Smile className="h-4 w-4" />
          </Button>
        )}
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 border-0 shadow-lg" align="start">
        <Picker
          data={data}
          onEmojiSelect={handleEmojiSelect}
          theme="light"
          previewPosition="none"
          searchPosition="none"
          skinTonePosition="none"
          perLine={8}
          emojiSize={24}
          emojiButtonSize={36}
          maxFrequentRows={1}
        />
      </PopoverContent>
    </Popover>
  );
};
