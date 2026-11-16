// Private music streaming from a Cloudflare R2 bucket.
// Every request needs ?k=<ACCESS_KEY> (a secret set with `wrangler secret put ACCESS_KEY`).
//   GET /index        -> {files:[{key,size}]}   list of songs in the bucket
//   GET /file/<key>   -> audio, with Range support (phones need it for seeking/streaming)
// Bucket layout: tracks/<library id>.<ext> for songs in the library, extra/<Artist - Title>.<ext> for others.

const ALLOWED_ORIGINS = ['https://aweb961-lang.github.io', 'http://localhost:8767'];

function cors(req) {
  const o = req.headers.get('Origin');
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(o) ? o : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Headers': 'Range',
    'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Accept-Ranges',
    'Vary': 'Origin',
  };
}

function sameKey(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const h = cors(req);
    if (req.method === 'OPTIONS') return new Response(null, { headers: h });
    if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('Method not allowed', { status: 405, headers: h });
    if (!sameKey(url.searchParams.get('k'), env.ACCESS_KEY)) return new Response('Wrong or missing key', { status: 401, headers: h });

    if (url.pathname === '/index') {
      const files = [];
      let cursor;
      do {
        const page = await env.MUSIC.list({ cursor, limit: 1000 });
        page.objects.forEach(o => files.push({ key: o.key, size: o.size }));
        cursor = page.truncated ? page.cursor : undefined;
      } while (cursor);
      return Response.json({ files }, { headers: { ...h, 'Cache-Control': 'no-store' } });
    }

    if (url.pathname.startsWith('/file/')) {
      const key = decodeURIComponent(url.pathname.slice(6));
      const range = req.headers.get('Range');
      const head = await env.MUSIC.head(key);
      if (!head) return new Response('Not found', { status: 404, headers: h });
      const size = head.size;
      const headers = { ...h, 'Accept-Ranges': 'bytes', 'Content-Type': head.httpMetadata?.contentType || 'audio/mpeg',
                        'Cache-Control': 'private, max-age=86400', 'ETag': head.httpEtag };
      const m = range && range.match(/bytes=(\d*)-(\d*)/);
      if (m) {
        let start = m[1] === '' ? size - Number(m[2]) : Number(m[1]);
        let end = m[1] !== '' && m[2] !== '' ? Number(m[2]) : size - 1;
        if (start < 0) start = 0;
        if (end >= size) end = size - 1;
        if (start > end) return new Response(null, { status: 416, headers: { ...headers, 'Content-Range': `bytes */${size}` } });
        const obj = await env.MUSIC.get(key, { range: { offset: start, length: end - start + 1 } });
        return new Response(req.method === 'HEAD' ? null : obj.body, { status: 206,
          headers: { ...headers, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': String(end - start + 1) } });
      }
      const obj = await env.MUSIC.get(key);
      return new Response(req.method === 'HEAD' ? null : obj.body, { headers: { ...headers, 'Content-Length': String(size) } });
    }
    return new Response('Not found', { status: 404, headers: h });
  },
};
