import { describe, it, expect } from 'vitest';
import { parseSseLine } from '../api.js';

describe('parseSseLine', () => {
  it('parses token event', () => {
    expect(parseSseLine('data: {"type":"token","text":"hi"}')).toEqual({ type: 'token', text: 'hi' });
  });
  it('parses sources event', () => {
    const line = 'data: {"type":"sources","sources":[{"page_number":3,"text":"abc"}]}';
    expect(parseSseLine(line)).toEqual({ type: 'sources', sources: [{ page_number: 3, text: 'abc' }] });
  });
  it('maps [DONE] to done event', () => {
    expect(parseSseLine('data: [DONE]')).toEqual({ type: 'done' });
  });
  it('returns null for non-data lines', () => {
    expect(parseSseLine(': heartbeat')).toBeNull();
  });
});
