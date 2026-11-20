import type { ChoiceItem } from '../components/Inputs';
import type { Option } from '../api';
import { GLOSS } from './content';

/** Engine option tuples → ChoiceGroup items, with glosses from content.ts where one exists. */
export function toItems(options: Option[], glossKey?: keyof typeof GLOSS, exclude: string[] = []): ChoiceItem[] {
  const gloss = glossKey ? GLOSS[glossKey] : undefined;
  return options
    .filter(([key]) => !exclude.includes(key))
    .map(([key, label]) => {
      // Engine labels often read "Name — explanation"; split that into label + sub.
      const [head, ...rest] = label.split(' — ');
      return { value: key, label: head, sub: gloss?.[key] ?? (rest.join(' — ') || undefined) };
    });
}
