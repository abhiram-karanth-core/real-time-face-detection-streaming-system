import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app title', () => {
  render(<App />);
  const linkElement = screen.getByText(/Real-Time Face Detection/i);
  expect(linkElement).toBeInTheDocument();
});
