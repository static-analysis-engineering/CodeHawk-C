/* Mirrors the relevant ColorDodge expression from ImageMagick

   Ref Issue #78: https://github.com/static-analysis-engineering/CodeHawk-C/issues/78
*/

typedef double MagickRealType;

static MagickRealType ColorDodge(
    const MagickRealType Sca,
    const MagickRealType Sa,
    const MagickRealType Dca,
    const MagickRealType Da) {
  if ((Sca * Da + Dca * Sa) >= Sa * Da) {
    return Sa * Da + Sca * (1.0 - Da) + Dca * (1.0 - Sa);
  }
  return Dca * Sa * Sa / (Sa - Sca) + Sca * (1.0 - Da) + Dca * (1.0 - Sa);
}

int main(void) {
  return ColorDodge(0.1, 0.5, 0.2, 0.7) > 0.0;
}
