const Parser = require('rss-parser');
const axios = require('axios');
console.log("=== スクリプト開始 ===");

const parser = new Parser();

const FEEDS = [
  'http://feeds.bbci.co.uk/news/rss.xml',
  'https://www3.nhk.or.jp/rss/news/cat0.xml',
  'http://export.arxiv.org/rss/cs'
];



async function postToSanity({title, summary, url, tags}) {
  console.log("Sanity投稿開始:", title);
  try {
    await axios.post(
      `https://${process.env.SANITY_PROJECT_ID}.api.sanity.io/v2021-10-21/data/mutate/production`,
      {
        mutations: [{
          create: {
            _type: 'article',
            title,
            summary,
            url,
            tags
          }
        }]
      },
      {
        headers: {
          Authorization: `Bearer ${process.env.SANITY_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    console.log("Sanity投稿成功:", title);
  } catch (error) {
    console.error("Sanity投稿失敗:", title, error.response?.data || error.message);
  }
}

async function main() {
  let allItems = [];
  for (const feedUrl of FEEDS) {
    console.log("RSS取得開始:", feedUrl);
    const feed = await parser.parseURL(feedUrl);
    console.log("取得記事数:", feed.items.length, "URL:", feedUrl);
    allItems.push(...feed.items);
  }
  allItems = allItems
    .sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate))
    .slice(0, 3); // 最新3件だけ

  console.log("最新記事数:", allItems.length);

  for (const item of allItems) {
    console.log("記事処理開始:", item.title);
    const tags = [];
    await postToSanity({
      title: item.title,
      body: `引用元: [${item.title}](${item.link})`,
      tags
    });
    console.log("記事処理完了:", item.title);
  }
}

main().catch((error) => {
  console.error("スクリプト全体でエラー:", error);
});