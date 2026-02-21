import type { Card, Suit } from '../api/types';

const SUIT_SYMBOLS: Record<Suit, string> = {
  Hearts: '♥',
  Diamonds: '♦',
  Clubs: '♣',
  Spades: '♠',
};

export function suitSymbol(suit: Suit): string {
  return SUIT_SYMBOLS[suit];
}

export function isRed(suit: Suit): boolean {
  return suit === 'Hearts' || suit === 'Diamonds';
}

export function cardLabel(card: Card): string {
  return `${card.rank}${SUIT_SYMBOLS[card.suit]}`;
}

export function cardKey(card: Card): string {
  return `${card.rank}-${card.suit}`;
}
