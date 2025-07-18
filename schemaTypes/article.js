export default {
  name: 'article',
  title: 'まとめ記事',
  type: 'document',
  fields: [
    {
      name: 'title',
      title: 'タイトル',
      type: 'string',
    },
    {
      name: 'body',
      title: '本文',
      type: 'text',
    },
    {
      name: 'mainImage',
      title: '画像',
      type: 'image',
      options: {
        hotspot: true,
      },
    },
    {
      name: 'publishedAt',
      title: '投稿日',
      type: 'datetime',
    },
    {
      name: 'tags',
      title: 'タグ',
      type: 'array',
      of: [{ type: 'string' }],
    },
  ],
};