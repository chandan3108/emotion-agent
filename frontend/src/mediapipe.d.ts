// Suppress TypeScript errors for dynamic MediaPipe imports
declare module "/mediapipe/vision_bundle.js" {
  const content: any;
  export default content;
  export const FilesetResolver: any;
  export const FaceLandmarker: any;
}
