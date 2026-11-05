import React from 'react';
import { Composition } from 'remotion';
import { CUADROS, Video } from './Video';
// 9:16 vertical, 1080×1920 a 30 cuadros por segundo. La duración sale de tiempos.json.
export const Root: React.FC = () => (
  <Composition id="Video" component={Video} durationInFrames={CUADROS} fps={30} width={1080} height={1920} />
);
