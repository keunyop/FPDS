import { ImageResponse } from 'next/og';

export const alt = 'EQ Bank, Tangerine and TD savings account comparison — SwitchaBank';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function Image() {
  return new ImageResponse(<div style={{ display: 'flex', width: '100%', height: '100%', flexDirection: 'column', justifyContent: 'space-between', padding: 70, background: '#f4f1e9', color: '#1c2723' }}>
    <div style={{ display: 'flex', fontSize: 27, color: '#176b55' }}>SwitchaBank / Blog</div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', fontSize: 66, fontWeight: 700, lineHeight: 1.1 }}>Read beyond the headline rate.</div>
      <div style={{ display: 'flex', fontSize: 34 }}>EQ Bank · Tangerine · TD</div>
    </div>
    <div style={{ display: 'flex', borderTop: '2px solid #d8d4ca', paddingTop: 25, fontSize: 24 }}>Canadian savings accounts / Fees, conditions and comparisons</div>
  </div>, size);
}
