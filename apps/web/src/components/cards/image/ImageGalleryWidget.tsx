interface ImageGalleryWidgetProps {
  payload: Record<string, unknown>;
}

export function ImageGalleryWidget({ payload }: ImageGalleryWidgetProps) {
  const url = String(payload.url ?? payload.image_url ?? "");
  const alt = String(payload.alt ?? "Generated image");
  const images = (payload.images as Array<{ url: string; alt?: string }>) ?? [];

  if (images.length) {
    return (
      <div className="grid grid-cols-2 gap-2">
        {images.map((img, i) => (
          <img key={i} src={img.url} alt={img.alt ?? alt} className="rounded-lg object-cover w-full" />
        ))}
      </div>
    );
  }

  if (url) {
    return <img src={url} alt={alt} className="rounded-lg max-h-64 object-contain w-full" />;
  }

  return <p className="text-sm text-on-surface-variant">Generating image…</p>;
}
