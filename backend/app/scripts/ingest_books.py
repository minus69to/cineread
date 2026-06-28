"""
Ingest a curated set of well-known books into ChromaDB with LLM enrichment.
No external API required for the book list — titles are curated, LLM fills in rich metadata.
Run from backend/: python -m app.scripts.ingest_books
"""
import asyncio
import json
import re

import chromadb
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.config import settings

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 50
LLM_DELAY = 0.35

# fmt: off
BOOK_SEED: list[dict] = [
    # ── Self-help / Personal Development ──────────────────────────────────────
    {"title": "Atomic Habits", "author": "James Clear", "year": 2018, "genre": "Self-help, Productivity"},
    {"title": "Ikigai", "author": "Héctor García, Francesc Miralles", "year": 2016, "genre": "Self-help, Japanese Philosophy"},
    {"title": "Man's Search for Meaning", "author": "Viktor E. Frankl", "year": 1946, "genre": "Psychology, Philosophy, Memoir"},
    {"title": "The Courage to Be Disliked", "author": "Ichiro Kishimi, Fumitake Koga", "year": 2013, "genre": "Self-help, Adlerian Psychology"},
    {"title": "The Things You Can See Only When You Slow Down", "author": "Haemin Sunim", "year": 2012, "genre": "Mindfulness, Self-help"},
    {"title": "The Daily Stoic", "author": "Ryan Holiday", "year": 2016, "genre": "Philosophy, Stoicism, Self-help"},
    {"title": "Essentialism", "author": "Greg McKeown", "year": 2014, "genre": "Productivity, Self-help, Business"},
    {"title": "Four Thousand Weeks", "author": "Oliver Burkeman", "year": 2021, "genre": "Time Management, Philosophy, Self-help"},
    {"title": "The Almanack of Naval Ravikant", "author": "Eric Jorgenson", "year": 2020, "genre": "Self-help, Business, Philosophy"},
    {"title": "Deep Work", "author": "Cal Newport", "year": 2016, "genre": "Productivity, Self-help"},
    {"title": "Digital Minimalism", "author": "Cal Newport", "year": 2019, "genre": "Self-help, Technology"},
    {"title": "The Power of Habit", "author": "Charles Duhigg", "year": 2012, "genre": "Psychology, Self-help, Neuroscience"},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "year": 2011, "genre": "Psychology, Behavioral Economics"},
    {"title": "How to Win Friends and Influence People", "author": "Dale Carnegie", "year": 1936, "genre": "Self-help, Communication"},
    {"title": "The 7 Habits of Highly Effective People", "author": "Stephen R. Covey", "year": 1989, "genre": "Self-help, Business, Leadership"},
    {"title": "The 48 Laws of Power", "author": "Robert Greene", "year": 1998, "genre": "Self-help, Strategy, History"},
    {"title": "Mindset: The New Psychology of Success", "author": "Carol S. Dweck", "year": 2006, "genre": "Psychology, Self-help, Education"},
    {"title": "Flow: The Psychology of Optimal Experience", "author": "Mihaly Csikszentmihalyi", "year": 1990, "genre": "Psychology, Self-help"},
    {"title": "Grit", "author": "Angela Duckworth", "year": 2016, "genre": "Self-help, Psychology"},
    {"title": "The Subtle Art of Not Giving a F*ck", "author": "Mark Manson", "year": 2016, "genre": "Self-help, Philosophy"},
    {"title": "Never Split the Difference", "author": "Chris Voss", "year": 2016, "genre": "Negotiation, Business, Self-help"},
    {"title": "The Psychology of Money", "author": "Morgan Housel", "year": 2020, "genre": "Finance, Personal Development"},
    {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari", "year": 2011, "genre": "History, Anthropology, Non-fiction"},
    {"title": "Homo Deus: A Brief History of Tomorrow", "author": "Yuval Noah Harari", "year": 2015, "genre": "Futurism, History, Technology"},
    {"title": "Zero to One", "author": "Peter Thiel", "year": 2014, "genre": "Business, Entrepreneurship, Technology"},
    {"title": "Outliers: The Story of Success", "author": "Malcolm Gladwell", "year": 2008, "genre": "Self-help, Sociology, Non-fiction"},
    {"title": "Blink: The Power of Thinking Without Thinking", "author": "Malcolm Gladwell", "year": 2005, "genre": "Psychology, Non-fiction"},
    {"title": "Feel-Good Productivity", "author": "Ali Abdaal", "year": 2023, "genre": "Productivity, Self-help"},
    {"title": "The Body Keeps the Score", "author": "Bessel van der Kolk", "year": 2014, "genre": "Psychology, Trauma, Mental Health"},
    {"title": "When Breath Becomes Air", "author": "Paul Kalanithi", "year": 2016, "genre": "Memoir, Medicine, Philosophy"},
    {"title": "Being Mortal", "author": "Atul Gawande", "year": 2014, "genre": "Medicine, Philosophy, Aging"},
    {"title": "Lost Connections", "author": "Johann Hari", "year": 2018, "genre": "Mental Health, Psychology, Non-fiction"},
    # ── Mindfulness / Spirituality ─────────────────────────────────────────────
    {"title": "The Power of Now", "author": "Eckhart Tolle", "year": 1997, "genre": "Spirituality, Mindfulness, Self-help"},
    {"title": "A New Earth", "author": "Eckhart Tolle", "year": 2005, "genre": "Spirituality, Mindfulness"},
    {"title": "The Art of Happiness", "author": "Dalai Lama, Howard C. Cutler", "year": 1998, "genre": "Buddhism, Mindfulness, Self-help"},
    {"title": "When Things Fall Apart", "author": "Pema Chödrön", "year": 1997, "genre": "Buddhism, Mindfulness, Self-help"},
    {"title": "The Gifts of Imperfection", "author": "Brené Brown", "year": 2010, "genre": "Self-help, Psychology, Mindfulness"},
    {"title": "Daring Greatly", "author": "Brené Brown", "year": 2012, "genre": "Self-help, Psychology"},
    {"title": "Why Buddhism is True", "author": "Robert Wright", "year": 2017, "genre": "Buddhism, Psychology, Science"},
    {"title": "Why We Sleep", "author": "Matthew Walker", "year": 2017, "genre": "Science, Health, Psychology"},
    # ── Science Fiction ────────────────────────────────────────────────────────
    {"title": "Dune", "author": "Frank Herbert", "year": 1965, "genre": "Science Fiction, Epic, Adventure"},
    {"title": "Foundation", "author": "Isaac Asimov", "year": 1951, "genre": "Science Fiction, Space Opera"},
    {"title": "1984", "author": "George Orwell", "year": 1949, "genre": "Dystopia, Political Fiction, Science Fiction"},
    {"title": "Brave New World", "author": "Aldous Huxley", "year": 1932, "genre": "Dystopia, Science Fiction, Philosophy"},
    {"title": "Fahrenheit 451", "author": "Ray Bradbury", "year": 1953, "genre": "Dystopia, Science Fiction"},
    {"title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "year": 1979, "genre": "Science Fiction, Comedy, Satire"},
    {"title": "Ender's Game", "author": "Orson Scott Card", "year": 1985, "genre": "Science Fiction, Military, Adventure"},
    {"title": "The Martian", "author": "Andy Weir", "year": 2011, "genre": "Science Fiction, Survival, Comedy"},
    {"title": "Project Hail Mary", "author": "Andy Weir", "year": 2021, "genre": "Science Fiction, Space, Survival"},
    {"title": "The Three-Body Problem", "author": "Liu Cixin", "year": 2008, "genre": "Science Fiction, Hard Science Fiction, Chinese Literature"},
    {"title": "Dark Matter", "author": "Blake Crouch", "year": 2016, "genre": "Science Fiction, Thriller, Quantum Physics"},
    {"title": "Recursion", "author": "Blake Crouch", "year": 2019, "genre": "Science Fiction, Thriller, Memory"},
    {"title": "Annihilation", "author": "Jeff VanderMeer", "year": 2014, "genre": "Science Fiction, Horror, Mystery"},
    {"title": "The Handmaid's Tale", "author": "Margaret Atwood", "year": 1985, "genre": "Dystopia, Feminist Fiction, Science Fiction"},
    {"title": "Never Let Me Go", "author": "Kazuo Ishiguro", "year": 2005, "genre": "Science Fiction, Literary Fiction, Ethics"},
    {"title": "Klara and the Sun", "author": "Kazuo Ishiguro", "year": 2021, "genre": "Science Fiction, Literary Fiction, AI"},
    {"title": "Station Eleven", "author": "Emily St. John Mandel", "year": 2014, "genre": "Post-apocalyptic, Science Fiction, Literary"},
    {"title": "The Road", "author": "Cormac McCarthy", "year": 2006, "genre": "Post-apocalyptic, Literary Fiction, Survival"},
    {"title": "Flowers for Algernon", "author": "Daniel Keyes", "year": 1966, "genre": "Science Fiction, Psychology, Literary"},
    {"title": "Do Androids Dream of Electric Sheep?", "author": "Philip K. Dick", "year": 1968, "genre": "Science Fiction, Philosophy, Dystopia"},
    {"title": "Solaris", "author": "Stanisław Lem", "year": 1961, "genre": "Science Fiction, Philosophy, Hard Science Fiction"},
    # ── Thriller / Mystery ─────────────────────────────────────────────────────
    {"title": "Gone Girl", "author": "Gillian Flynn", "year": 2012, "genre": "Psychological Thriller, Mystery, Crime"},
    {"title": "Sharp Objects", "author": "Gillian Flynn", "year": 2006, "genre": "Psychological Thriller, Crime, Dark"},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "year": 2005, "genre": "Crime, Mystery, Thriller"},
    {"title": "The Silent Patient", "author": "Alex Michaelides", "year": 2019, "genre": "Psychological Thriller, Mystery"},
    {"title": "And Then There Were None", "author": "Agatha Christie", "year": 1939, "genre": "Mystery, Classic Crime, Thriller"},
    {"title": "Murder on the Orient Express", "author": "Agatha Christie", "year": 1934, "genre": "Mystery, Classic Crime, Detective"},
    {"title": "In the Woods", "author": "Tana French", "year": 2007, "genre": "Crime, Mystery, Psychological Thriller"},
    {"title": "The Girl on the Train", "author": "Paula Hawkins", "year": 2015, "genre": "Psychological Thriller, Mystery, Crime"},
    {"title": "Big Little Lies", "author": "Liane Moriarty", "year": 2014, "genre": "Mystery, Thriller, Domestic Drama"},
    {"title": "The Shining", "author": "Stephen King", "year": 1977, "genre": "Horror, Psychological Horror, Thriller"},
    {"title": "It", "author": "Stephen King", "year": 1986, "genre": "Horror, Coming-of-age, Supernatural"},
    {"title": "Misery", "author": "Stephen King", "year": 1987, "genre": "Horror, Thriller, Psychological"},
    {"title": "Verity", "author": "Colleen Hoover", "year": 2018, "genre": "Psychological Thriller, Dark Romance, Mystery"},
    {"title": "The Thursday Murder Club", "author": "Richard Osman", "year": 2020, "genre": "Cozy Mystery, Comedy, Crime"},
    {"title": "The 7½ Deaths of Evelyn Hardcastle", "author": "Stuart Turton", "year": 2018, "genre": "Mystery, Time Loop, Historical"},
    {"title": "The Da Vinci Code", "author": "Dan Brown", "year": 2003, "genre": "Thriller, Mystery, Historical, Adventure"},
    {"title": "Behind Closed Doors", "author": "B.A. Paris", "year": 2016, "genre": "Psychological Thriller, Domestic Suspense"},
    # ── Literary Fiction ───────────────────────────────────────────────────────
    {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "year": 1866, "genre": "Literary Fiction, Psychological, Russian Classic"},
    {"title": "The Brothers Karamazov", "author": "Fyodor Dostoevsky", "year": 1880, "genre": "Literary Fiction, Philosophy, Russian Classic"},
    {"title": "The Master and Margarita", "author": "Mikhail Bulgakov", "year": 1967, "genre": "Magical Realism, Satire, Russian Fiction"},
    {"title": "100 Years of Solitude", "author": "Gabriel García Márquez", "year": 1967, "genre": "Magical Realism, Literary Fiction, Latin American"},
    {"title": "The Stranger", "author": "Albert Camus", "year": 1942, "genre": "Existentialist, Literary Fiction, Philosophical"},
    {"title": "Kafka on the Shore", "author": "Haruki Murakami", "year": 2002, "genre": "Magical Realism, Literary Fiction, Japanese"},
    {"title": "Norwegian Wood", "author": "Haruki Murakami", "year": 1987, "genre": "Literary Fiction, Romance, Japanese"},
    {"title": "The Wind-Up Bird Chronicle", "author": "Haruki Murakami", "year": 1994, "genre": "Magical Realism, Literary Fiction, Mystery"},
    {"title": "1Q84", "author": "Haruki Murakami", "year": 2009, "genre": "Magical Realism, Mystery, Literary Fiction"},
    {"title": "Siddhartha", "author": "Hermann Hesse", "year": 1922, "genre": "Philosophy, Spiritual, Literary Fiction"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "year": 1951, "genre": "Literary Fiction, Coming-of-age, Classic"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "year": 1960, "genre": "Literary Fiction, Historical, Social Justice"},
    {"title": "East of Eden", "author": "John Steinbeck", "year": 1952, "genre": "Literary Fiction, Epic, American Classic"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "year": 1925, "genre": "Literary Fiction, American Classic, Tragedy"},
    {"title": "Lord of the Flies", "author": "William Golding", "year": 1954, "genre": "Literary Fiction, Psychological, Dystopia"},
    {"title": "A Little Life", "author": "Hanya Yanagihara", "year": 2015, "genre": "Literary Fiction, Trauma, Dark, Friendship"},
    {"title": "The Secret History", "author": "Donna Tartt", "year": 1992, "genre": "Literary Fiction, Thriller, Dark Academia"},
    {"title": "Normal People", "author": "Sally Rooney", "year": 2018, "genre": "Literary Fiction, Romance, Contemporary"},
    {"title": "Piranesi", "author": "Susanna Clarke", "year": 2020, "genre": "Magical Realism, Mystery, Fantasy, Literary"},
    {"title": "Beloved", "author": "Toni Morrison", "year": 1987, "genre": "Literary Fiction, Historical, Magical Realism"},
    {"title": "Anna Karenina", "author": "Leo Tolstoy", "year": 1878, "genre": "Literary Fiction, Romance, Russian Classic"},
    {"title": "The Idiot", "author": "Fyodor Dostoevsky", "year": 1869, "genre": "Literary Fiction, Philosophical, Russian Classic"},
    {"title": "Pachinko", "author": "Min Jin Lee", "year": 2017, "genre": "Historical Fiction, Literary, Korean, Family Saga"},
    {"title": "Everything I Never Told You", "author": "Celeste Ng", "year": 2014, "genre": "Literary Fiction, Family Drama, Mystery"},
    {"title": "The Kite Runner", "author": "Khaled Hosseini", "year": 2003, "genre": "Literary Fiction, Historical, Redemption"},
    {"title": "A Thousand Splendid Suns", "author": "Khaled Hosseini", "year": 2007, "genre": "Literary Fiction, Historical, Women's Fiction"},
    # ── Biography / Memoir ─────────────────────────────────────────────────────
    {"title": "Educated", "author": "Tara Westover", "year": 2018, "genre": "Memoir, Self-discovery, Coming-of-age"},
    {"title": "Becoming", "author": "Michelle Obama", "year": 2018, "genre": "Memoir, Biography, Inspirational"},
    {"title": "The Glass Castle", "author": "Jeannette Walls", "year": 2005, "genre": "Memoir, Family, Coming-of-age"},
    {"title": "Born a Crime", "author": "Trevor Noah", "year": 2016, "genre": "Memoir, Comedy, Apartheid, Coming-of-age"},
    {"title": "The Diary of a Young Girl", "author": "Anne Frank", "year": 1947, "genre": "Diary, Historical, World War II, Coming-of-age"},
    {"title": "Night", "author": "Elie Wiesel", "year": 1960, "genre": "Memoir, Holocaust, Historical"},
    {"title": "Shoe Dog", "author": "Phil Knight", "year": 2016, "genre": "Memoir, Business, Entrepreneurship"},
    {"title": "I Know Why the Caged Bird Sings", "author": "Maya Angelou", "year": 1969, "genre": "Memoir, Coming-of-age, Race"},
    {"title": "Wild", "author": "Cheryl Strayed", "year": 2012, "genre": "Memoir, Nature, Self-discovery"},
    {"title": "Surely You're Joking, Mr. Feynman!", "author": "Richard P. Feynman", "year": 1985, "genre": "Biography, Science, Humor"},
    # ── Philosophy ─────────────────────────────────────────────────────────────
    {"title": "Meditations", "author": "Marcus Aurelius", "year": 180, "genre": "Philosophy, Stoicism, Classic"},
    {"title": "Letters from a Stoic", "author": "Seneca", "year": 65, "genre": "Philosophy, Stoicism, Classic"},
    {"title": "The Myth of Sisyphus", "author": "Albert Camus", "year": 1942, "genre": "Philosophy, Existentialism, Essay"},
    {"title": "Walden", "author": "Henry David Thoreau", "year": 1854, "genre": "Philosophy, Nature, Minimalism"},
    {"title": "The Art of War", "author": "Sun Tzu", "year": -500, "genre": "Philosophy, Strategy, Classic"},
    {"title": "Thus Spoke Zarathustra", "author": "Friedrich Nietzsche", "year": 1883, "genre": "Philosophy, Existentialism"},
    {"title": "Justice: What's the Right Thing to Do?", "author": "Michael Sandel", "year": 2009, "genre": "Philosophy, Ethics, Political"},
    {"title": "The Better Angels of Our Nature", "author": "Steven Pinker", "year": 2011, "genre": "History, Psychology, Science"},
    # ── Fantasy ────────────────────────────────────────────────────────────────
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "year": 1954, "genre": "Fantasy, Epic, Adventure"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "year": 1937, "genre": "Fantasy, Adventure, Classic"},
    {"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling", "year": 1997, "genre": "Fantasy, Coming-of-age, Magic"},
    {"title": "A Game of Thrones", "author": "George R.R. Martin", "year": 1996, "genre": "Fantasy, Epic, Political Intrigue"},
    {"title": "The Name of the Wind", "author": "Patrick Rothfuss", "year": 2007, "genre": "Fantasy, Epic, Coming-of-age"},
    {"title": "American Gods", "author": "Neil Gaiman", "year": 2001, "genre": "Fantasy, Mythology, Road Novel"},
    {"title": "The Night Circus", "author": "Erin Morgenstern", "year": 2011, "genre": "Fantasy, Magical Realism, Romance"},
    {"title": "Jonathan Strange & Mr Norrell", "author": "Susanna Clarke", "year": 2004, "genre": "Fantasy, Historical, Literary"},
    {"title": "The Way of Kings", "author": "Brandon Sanderson", "year": 2010, "genre": "Fantasy, Epic, World-building"},
    # ── Popular Science ─────────────────────────────────────────────────────────
    {"title": "A Brief History of Time", "author": "Stephen Hawking", "year": 1988, "genre": "Popular Science, Physics, Cosmology"},
    {"title": "The Selfish Gene", "author": "Richard Dawkins", "year": 1976, "genre": "Biology, Evolution, Popular Science"},
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "year": 1997, "genre": "History, Anthropology, Popular Science"},
    {"title": "The Emperor of All Maladies", "author": "Siddhartha Mukherjee", "year": 2010, "genre": "Medicine, History, Popular Science"},
    {"title": "Hidden Figures", "author": "Margot Lee Shetterly", "year": 2016, "genre": "History, Science, Biography"},
    {"title": "A Short History of Nearly Everything", "author": "Bill Bryson", "year": 2003, "genre": "Popular Science, History, Humor"},
    {"title": "Freakonomics", "author": "Steven D. Levitt, Stephen J. Dubner", "year": 2005, "genre": "Economics, Sociology, Popular Science"},
    {"title": "The Information", "author": "James Gleick", "year": 2011, "genre": "History, Technology, Popular Science"},
]
# fmt: on


def _llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://cineread.app", "X-Title": "CineRead"},
    )


async def _llm_enrich(llm: AsyncOpenAI, book: dict) -> dict:
    prompt = f"""Book: {book['title']} ({book['year']})
Author: {book['author']}
Genre: {book['genre']}

Return ONLY valid JSON (no markdown):
{{
  "themes": ["5-8 specific narrative/conceptual themes e.g. purpose, identity, trauma, redemption, revenge"],
  "mood": ["3-5 mood descriptors e.g. inspiring, dark, melancholic, tense, contemplative, hopeful"],
  "style": ["2-4 style descriptors e.g. accessible non-fiction, lyrical prose, fast-paced thriller, philosophy for everyday life"],
  "keywords": ["5-8 search keywords e.g. Japanese wisdom, habit formation, unreliable narrator, post-apocalyptic, found family"],
  "similar_to": ["3-5 specific book titles that are genuinely similar in feel or audience — name real books"],
  "audience": ["2-4 reader profiles e.g. self-improvement seekers, fans of psychological fiction, philosophy enthusiasts, Korean drama fans"]
}}"""

    try:
        resp = await llm.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=450,
        )
        text = resp.choices[0].message.content or ""
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"    LLM enrichment failed for '{book['title']}': {e}")
        return {}


def _build_doc(book: dict, enrichment: dict) -> str:
    parts = [
        f"Title: {book['title']} ({book['year']})",
        f"Author: {book['author']}",
        f"Genre: {book['genre']}",
    ]

    if enrichment.get("themes"):
        parts.append(f"Themes: {', '.join(enrichment['themes'])}")
    if enrichment.get("mood"):
        parts.append(f"Mood: {', '.join(enrichment['mood'])}")
    if enrichment.get("style"):
        parts.append(f"Style: {', '.join(enrichment['style'])}")
    if enrichment.get("keywords"):
        parts.append(f"Keywords: {', '.join(enrichment['keywords'])}")
    if enrichment.get("similar_to"):
        parts.append(f"Similar to: {', '.join(enrichment['similar_to'])}")
    if enrichment.get("audience"):
        parts.append(f"Audience: {', '.join(enrichment['audience'])}")

    return "\n".join(p for p in parts if p.strip())


async def main() -> None:
    print("=== CineRead Book Ingest (curated list + LLM enrichment) ===")
    print(f"Books to ingest: {len(BOOK_SEED)}")

    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to ChromaDB...")
    chroma = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    collection = chroma.get_or_create_collection("books")
    print(f"Collection currently has {collection.count()} books. Will upsert all.\n")

    docs, metas, ids = [], [], []
    ingested = errors = 0
    llm = _llm_client()

    for i, book in enumerate(BOOK_SEED, 1):
        # ID: sanitized title slug
        slug = re.sub(r"[^a-z0-9]+", "_", book["title"].lower()).strip("_")
        item_id = f"book_{slug}"

        try:
            enrichment = await _llm_enrich(llm, book)
            await asyncio.sleep(LLM_DELAY)

            doc = _build_doc(book, enrichment)

            docs.append(doc)
            metas.append({
                "type": "book",
                "title": book["title"],
                "author": book["author"],
                "year": str(book["year"]),
                "genres": book["genre"],
                "rating": "",
                "cover_url": "",
                "ol_key": "",
            })
            ids.append(item_id)
            ingested += 1

            if i % 10 == 0 or i == len(BOOK_SEED):
                similar = enrichment.get("similar_to", [])[:3]
                print(f"  [{i}/{len(BOOK_SEED)}] {book['title']} → similar: {similar}")

            if len(docs) >= BATCH_SIZE:
                embs = model.encode(docs).tolist()
                collection.upsert(documents=docs, embeddings=embs, metadatas=metas, ids=ids)
                print(f"  Flushed batch. Total ingested: {ingested}")
                docs, metas, ids = [], [], []

        except Exception as e:
            print(f"  ERROR '{book['title']}': {e}")
            errors += 1

    if docs:
        embs = model.encode(docs).tolist()
        collection.upsert(documents=docs, embeddings=embs, metadatas=metas, ids=ids)

    print(f"\nDone! Ingested={ingested}, Errors={errors}")
    print(f"Total books in ChromaDB: {collection.count()}")


if __name__ == "__main__":
    asyncio.run(main())
