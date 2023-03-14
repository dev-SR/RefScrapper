# Citation Networks Scrapper

## Running Script

Install Environment:

```bash
pipenv sync/install
```

Activate Environment:

```bash
pipenv shell
```

Run Script:

```bash
python run.py <h> <n>
```

- `<h>` : optional, run headless? (`1[default]` or `0`)
- `<n>` : optional, number of pages to scrape (default: `1`)

## Notes

Only fetched ref info list for level 2; as we only need the ref list for level 2. We just need to get the paper info of level 3, not the ref list.