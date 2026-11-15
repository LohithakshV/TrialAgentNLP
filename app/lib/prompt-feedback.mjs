import { resources } from './resources.mjs';

export function promptFeedback(code) {
  const common = {
    code,
    example: 'For a fictional exercise, find asthma studies near Boston.',
    resource: resources.find(item => item.id === 'basics'),
  };
  if (code === 'off_topic') return {
    ...common,
    title: 'Let’s keep this about clinical research.',
    message: 'Describe a condition or research topic to explore study records. Your draft is still here to edit.',
  };
  if (code === 'needs_details') return {
    ...common,
    title: 'Which condition would you like to explore?',
    message: 'Add a condition to look up studies. For a general question about how trials work, the introduction below is a useful start.',
  };
  return null;
}
