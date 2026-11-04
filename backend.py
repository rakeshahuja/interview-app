"""
AI Interview Practice - BACKEND (English, AI + offline fallback)
Uses only Python's built-in libraries. No pip install needed.

Run:  python backend.py
Then open:  http://localhost:8000

- If Gemini works, answers are evaluated by AI.
- If Gemini is busy / slow / down, the app automatically falls back to an OFFLINE evaluator.
- Type  offline  in the API key box to use the offline evaluator directly.
"""
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = "gemini-3.8-flash"
ATTEMPTS = 2            # how many times to try Gemini
REQUEST_TIMEOUT = 30    # max seconds for one try
PORT = 8000
HERE = os.path.dirname(os.path.abspath(__file__))

QUESTIONS = {
    "Java": [
        "What is OOP? Explain its 4 pillars.",
        "What is the difference between an abstract class and an interface?",
        "How does exception handling work in Java?",
        "How does a HashMap work internally?",
        "Explain the difference between JVM, JRE and JDK.",
    ],
    "Python": [
        "What is the difference between a list and a tuple?",
        "What is a decorator in Python?",
        "How does memory management work in Python?",
        "What is the difference between generators and iterators?",
        "Explain exception handling in Python.",
    ],
    "HR": [
        "Tell me about yourself.",
        "What is your biggest strength and your biggest weakness?",
        "Why should we hire you?",
        "Describe a challenge you faced and how you solved it.",
        "Where do you see yourself in 5 years?",
    ],
    "JavaScript": [
        "What is the difference between var, let and const?",
        "What is the difference between == and ===?",
        "What is a closure in JavaScript?",
        "What is hoisting in JavaScript?",
        "Explain the event loop and the difference between synchronous and asynchronous code.",
    ],
    "SQL": [
        "What is the difference between a primary key and a foreign key?",
        "Explain the different types of SQL joins.",
        "What is normalization and why is it used?",
        "What is a subquery? Give an example.",
        "What is an index in SQL and when should you use it?",
    ],
    "DSA": [
        "What is the difference between an array and a linked list?",
        "What is the difference between a stack and a queue?",
        "What is the difference between BFS and DFS?",
        "What is a hash table and how does it handle collisions?",
        "What is a Binary Search Tree and why is searching in it efficient?",
    ],
}

# ---------------------------------------------------------------------------
# OFFLINE KNOWLEDGE BASE: model answer + key points for every question
# points = (label, [keywords that should appear in the answer])
# ---------------------------------------------------------------------------
KB_LIST = {
    "Java": [
        {
            "model": "OOP (Object-Oriented Programming) is a programming approach that organizes code into classes and objects. Its 4 pillars are: Encapsulation (bundling data and methods into one unit and hiding data, e.g. private variables), Inheritance (one class acquires the properties of another using extends), Polymorphism (the same method name behaves differently, via overloading and overriding), and Abstraction (showing only what is necessary and hiding implementation, using abstract classes or interfaces). Example: a Dog class inherits from an Animal class and overrides sound().",
            "points": [
                ("The concept of classes and objects", ["class", "object"]),
                ("Encapsulation", ["encapsulation", "encapsul"]),
                ("Inheritance", ["inheritance", "inherit", "extends"]),
                ("Polymorphism", ["polymorphism", "overload", "overrid"]),
                ("Abstraction", ["abstraction", "abstract"]),
            ],
        },
        {
            "model": "An abstract class can have both abstract and concrete methods, and it can also have variables, constructors and state. A class can extend only one abstract class. An interface defines a contract of methods (default and static methods are allowed in modern Java), and a class can implement many interfaces, which gives a form of multiple inheritance. Use an abstract class when related classes share common code, and an interface when you only need to define a contract. Example: Shape as an abstract class, Drawable as an interface.",
            "points": [
                ("Abstract class can have abstract and concrete methods", ["abstract class", "concrete", "normal method", "constructor"]),
                ("Interface defines a contract", ["interface", "contract", "declaration"]),
                ("Multiple inheritance via interfaces", ["multiple"]),
                ("extends vs implements", ["extends", "implements"]),
                ("When to use which / example", ["example", "for instance", "use when", "when "]),
            ],
        },
        {
            "model": "Java handles exceptions using try, catch, finally, throw and throws. Risky code goes in a try block, a catch block handles the error, and a finally block always runs (for example, to close resources). throw is used to raise an exception manually, and throws declares that a method may produce an exception. Exceptions are of two kinds: checked (verified at compile time, e.g. IOException) and unchecked (occur at runtime, e.g. NullPointerException).",
            "points": [
                ("try block", ["try"]),
                ("catch block", ["catch"]),
                ("finally block", ["finally"]),
                ("throw / throws", ["throw"]),
                ("Checked vs unchecked exceptions", ["checked", "unchecked", "runtime"]),
            ],
        },
        {
            "model": "A HashMap stores key-value pairs. The key's hashCode() is used to compute an index (bucket) in an internal array. If two keys land in the same bucket (a collision), they are stored in a linked list or a tree (since Java 8), and equals() is used to find the right key. When the number of entries crosses the load factor (default 0.75), the HashMap resizes and rehashes. On average, get and put take O(1) time.",
            "points": [
                ("Stores key-value pairs", ["key", "value"]),
                ("hashCode / hashing decides the bucket index", ["hash", "bucket", "index"]),
                ("Collision handling (linked list / tree)", ["collision", "linked list", "tree"]),
                ("equals() to match the key", ["equals"]),
                ("Load factor / resizing", ["load factor", "resize", "rehash", "0.75"]),
            ],
        },
        {
            "model": "The JVM (Java Virtual Machine) runs Java bytecode and provides platform independence. The JRE (Java Runtime Environment) contains the JVM plus the core libraries needed to run Java programs. The JDK (Java Development Kit) contains the JRE plus development tools such as the javac compiler and a debugger, which are needed to write and compile programs. In short: JDK contains JRE, and JRE contains JVM.",
            "points": [
                ("JVM runs bytecode", ["jvm", "bytecode", "virtual machine"]),
                ("JRE = JVM + libraries", ["jre", "library", "libraries", "runtime"]),
                ("JDK = JRE + development tools", ["jdk", "development"]),
                ("javac compiler / tools", ["javac", "compiler", "tools"]),
                ("Platform independence / relationship (JDK > JRE > JVM)", ["platform", "independent", "contains", "includes", "inside"]),
            ],
        },
    ],
    "Python": [
        {
            "model": "A list is mutable (it can be changed after creation, e.g. with append or remove) and is written with square brackets []. A tuple is immutable (it cannot be changed once created) and is written with round brackets (). Tuples are slightly faster and use less memory, and because they are hashable they can be used as dictionary keys. Example: use a tuple for fixed coordinates (10, 20) and a list for a shopping cart.",
            "points": [
                ("A list is mutable", ["mutable", "can be changed", "can change", "modify"]),
                ("A tuple is immutable", ["immutable", "cannot be changed", "can't be changed", "cannot change", "not change"]),
                ("Syntax: [] vs ()", ["[", "(", "bracket"]),
                ("Tuple is faster / uses less memory", ["fast", "memory", "speed"]),
                ("Example / hashable (dictionary key)", ["example", "for instance", "hashable", "dictionary", "key"]),
            ],
        },
        {
            "model": "A decorator is a function that takes another function as input and extends or changes its behavior without modifying the original code. It is applied with the @decorator_name syntax. Internally it creates a wrapper function (using a closure). Common uses are logging, timing and authentication. Example: adding @timer above a function measures how long it takes to run.",
            "points": [
                ("Takes a function and returns a new function", ["function"]),
                ("@ syntax", ["@"]),
                ("Wrapper / closure", ["wrapper", "closure", "inner"]),
                ("Changes behavior without modifying the original code", ["without", "behavior", "behaviour", "modify", "extend", "add"]),
                ("Example (logging / timer / auth)", ["example", "for instance", "logging", "timer", "timing", "auth"]),
            ],
        },
        {
            "model": "Python manages memory in a private heap, and the Python memory manager handles this automatically. Every object has a reference count; when the count drops to 0, the memory is freed. Cyclic references (for example two objects pointing to each other) are handled by the garbage collector (the gc module). Because of this, programmers do not need to free memory manually.",
            "points": [
                ("Private heap / memory manager", ["heap", "memory manager"]),
                ("Reference counting", ["reference", "count"]),
                ("Garbage collection", ["garbage", "gc"]),
                ("Cyclic references", ["cycl", "circular"]),
                ("It is automatic (no manual freeing)", ["automatic", "automatically", "manual"]),
            ],
        },
        {
            "model": "An iterator is an object that follows the iterator protocol (__iter__() and __next__()) and returns one element at a time. A generator is an easy way to create an iterator using the yield keyword. Generators are lazy: they produce values one by one only when needed, which saves memory on large data. Both are exhausted after one pass. Example: use a generator instead of a list for a million numbers.",
            "points": [
                ("yield keyword (generators)", ["yield"]),
                ("Lazy evaluation / saves memory", ["lazy", "memory"]),
                ("__iter__ and __next__ / iterator protocol", ["__iter__", "__next__", "next", "protocol"]),
                ("Exhausted after one use", ["once", "exhaust", "one time", "single"]),
                ("Example", ["example", "for instance", "million", "large"]),
            ],
        },
        {
            "model": "Python handles exceptions using try, except, else, finally and raise. Risky code goes in try, and the except block runs when an error occurs (it is better to catch specific exceptions such as ValueError or ZeroDivisionError). The else block runs if no error occurs, and finally always runs (for cleanup). raise is used to throw an exception manually.",
            "points": [
                ("try block", ["try"]),
                ("except block", ["except"]),
                ("finally block", ["finally"]),
                ("raise", ["raise"]),
                ("Specific exceptions / else / example", ["valueerror", "zerodivision", "specific", "else", "example", "for instance"]),
            ],
        },
    ],
    "HR": [
        {
            "model": "My name is [name]. I completed my [degree] from [college]. My main skills are [skills], and I have worked on projects such as [project]. I am interested in [field] because [reason]. I want to use my skills in this role and grow along with the company. (Keep it short, 1-2 minutes: education, skills, projects, goal.)",
            "points": [
                ("Education / background", ["college", "degree", "education", "btech", "b.tech", "student", "graduat", "engineering", "university"]),
                ("Skills", ["skill", "python", "java", "know", "language", "learned"]),
                ("Projects / experience", ["project", "internship", "experience", "built", "developed", "worked"]),
                ("Interest / goal", ["interest", "goal", "passion", "career", "future", "aspire", "want to"]),
                ("Short introduction (name / who you are)", ["i am", "my name", "myself", "i'm"]),
            ],
        },
        {
            "model": "My biggest strength is [strength], and I showed it when [example]. My weakness is [real weakness], but I am working on it by [what you are doing]. Be honest, pick a real weakness that is not critical for the job, and explain how you are improving.",
            "points": [
                ("States a clear strength", ["strength", "strong", "good at"]),
                ("Gives an example of the strength", ["example", "for instance", "project", "once", "when i"]),
                ("States a weakness", ["weakness", "weak", "struggle"]),
                ("Shows how they are improving", ["improv", "working on", "learn", "overcome", "practice"]),
                ("Honest and relevant to the job", ["honest", "job", "role"]),
            ],
        },
        {
            "model": "I have the skills required for this role, such as [skills], and I have used them in [project or experience]. I learn quickly and work well in a team. I can add value to the company by [value], and I am excited about [something specific about the company].",
            "points": [
                ("Relevant skills", ["skill", "python", "java", "technical", "knowledge"]),
                ("Value / contribution to the company", ["value", "contribute", "benefit", "help", "add"]),
                ("Ability to learn", ["learn", "adapt", "quick"]),
                ("Teamwork", ["team"]),
                ("Example / interest in the company", ["example", "for instance", "project", "company"]),
            ],
        },
        {
            "model": "Use the STAR format. Situation: [what was the problem]. Task: [what was my responsibility]. Action: [what steps I took]. Result: [what was the outcome and what I learned]. Example: a project was close to its deadline and a bug appeared; I divided the work with my team, fixed the bug and delivered on time.",
            "points": [
                ("Describes the situation / problem", ["problem", "challenge", "situation", "difficult", "issue", "deadline"]),
                ("Their own task / responsibility", ["task", "responsib", "my role", "i had to"]),
                ("The action they took", ["i ", "action", "steps", "solved", "fixed", "tried", "decided"]),
                ("The result / outcome", ["result", "outcome", "success", "completed", "delivered", "achieved"]),
                ("What they learned", ["learn", "lesson", "realized"]),
            ],
        },
        {
            "model": "In 5 years I want to be a skilled and experienced professional in my field. In the first years I will focus on learning and building a strong foundation, and later I would like to take on bigger responsibilities and possibly a team lead role. I want to grow with the company and contribute to its success.",
            "points": [
                ("Growth / learning", ["grow", "learn", "improve"]),
                ("Skills / expertise", ["skill", "expert", "experience", "knowledge"]),
                ("Role / leadership", ["lead", "senior", "manager", "role", "responsib"]),
                ("Contribution to the company", ["company", "contribute", "organization", "team"]),
                ("Clear goal / plan", ["goal", "plan", "aim", "target", "see myself"]),
            ],
        },
    ],
    "JavaScript": [
        {
            "model": "var is function-scoped, can be redeclared, and is hoisted and initialized with undefined. let and const are block-scoped (limited to the nearest { }) and are hoisted but cannot be used before their declaration (the temporal dead zone). let can be reassigned, while const cannot be reassigned after it is set (though the contents of a const object or array can still change). Best practice is to prefer const by default, use let when the value must change, and avoid var.",
            "points": [
                ("Scope: var is function-scoped, let and const are block-scoped", ["function-scoped", "function scope", "block-scoped", "block scope", "scope"]),
                ("Hoisting behavior (var is undefined, let/const have a temporal dead zone)", ["hoist", "undefined", "temporal", "tdz"]),
                ("const cannot be reassigned", ["reassign", "constant", "cannot be changed", "can't be changed"]),
                ("let can be reassigned; var can be redeclared", ["redeclar", "re-declar", "reassign"]),
                ("Example or best practice (prefer const / let, avoid var)", ["example", "for instance", "prefer", "recommend", "avoid", "best practice"]),
            ],
        },
        {
            "model": "== is the loose equality operator: it converts (coerces) the values to a common type before comparing, so 5 == '5' is true. === is the strict equality operator: it compares both value and type without any conversion, so 5 === '5' is false. Because type coercion can cause surprising bugs, it is recommended to use === almost always.",
            "points": [
                ("== is loose equality with type coercion", ["coerc", "loose", "type conversion", "converts"]),
                ("=== is strict equality (no conversion)", ["strict", "no conversion", "without conver"]),
                ("=== checks both value and type", ["type", "value"]),
                ("Example such as 5 == '5'", ["example", "for instance", "'5'", "\"5\"", "5 =="]),
                ("Recommendation: prefer ===", ["recommend", "prefer", "best practice", "avoid"]),
            ],
        },
        {
            "model": "A closure is a function that remembers the variables from the outer (lexical) scope where it was created, even after the outer function has finished running. For example, a makeCounter() function can return an inner function that keeps updating a private count variable. Closures are used for data privacy, counters, callbacks and function factories.",
            "points": [
                ("A function bundled with its outer scope", ["function"]),
                ("Lexical / outer scope", ["lexical", "outer", "scope"]),
                ("Remembers variables even after the outer function finishes", ["remember", "after", "even after", "retain", "access"]),
                ("Uses: data privacy, counters, callbacks", ["private", "privacy", "counter", "callback", "factory", "use case"]),
                ("Example", ["example", "for instance", "makecounter", "counter"]),
            ],
        },
        {
            "model": "Hoisting is JavaScript's behavior of moving declarations to the top of their scope during the creation phase, before the code runs. var variables are hoisted and initialized as undefined. Function declarations are fully hoisted, so they can be called before they appear in the code. let and const are hoisted too, but they stay in the temporal dead zone and throw a ReferenceError if used before their declaration.",
            "points": [
                ("Declarations are moved to the top of their scope", ["top", "moved", "move", "declaration"]),
                ("var is hoisted as undefined", ["var", "undefined"]),
                ("Function declarations are fully hoisted", ["function"]),
                ("let and const: temporal dead zone / ReferenceError", ["let", "const", "temporal", "tdz", "referenceerror", "error"]),
                ("Example", ["example", "for instance", "before"]),
            ],
        },
        {
            "model": "JavaScript is single-threaded and runs one piece of code at a time on the call stack. Synchronous code runs line by line and blocks the next line until it finishes. Asynchronous code (setTimeout, fetch, promises) is handed to Web APIs, and when it finishes its callback goes to a queue. The event loop keeps checking: when the call stack is empty it moves the next task from the queue to the stack, and microtasks (promise callbacks) run before regular tasks. This lets JavaScript handle slow operations without freezing.",
            "points": [
                ("JavaScript is single-threaded with a call stack", ["single-thread", "single thread", "call stack", "stack"]),
                ("Synchronous code is blocking and runs in order", ["synchronous", "blocking", "block", "in order"]),
                ("Asynchronous code (callbacks, promises, async/await, setTimeout)", ["asynchronous", "callback", "promise", "async", "settimeout", "fetch"]),
                ("Event loop moves tasks from the queue to the stack", ["event loop", "queue"]),
                ("Microtasks / Web APIs / non-blocking behavior", ["microtask", "web api", "non-blocking", "not block", "freez"]),
            ],
        },
    ],
    "SQL": [
        {
            "model": "A primary key uniquely identifies each row in a table. It must be unique and cannot be NULL, and a table can have only one primary key (which can span multiple columns). A foreign key is a column in one table that refers to the primary key of another table, and it creates a relationship between the two tables and enforces referential integrity. Example: in an Orders table, customer_id is a foreign key that points to the primary key id of the Customers table.",
            "points": [
                ("A primary key uniquely identifies each row", ["unique", "uniquely", "identif"]),
                ("A primary key cannot be NULL / only one per table", ["null", "only one", "one primary"]),
                ("A foreign key refers to another table's primary key", ["foreign key", "refer", "reference", "another table", "other table"]),
                ("Relationship between tables / referential integrity", ["relationship", "integrity", "link", "relation", "constraint"]),
                ("Example (Customers and Orders)", ["example", "for instance", "orders", "customer"]),
            ],
        },
        {
            "model": "A join combines rows from two or more tables based on a related column. INNER JOIN returns only the rows that match in both tables. LEFT JOIN returns all rows from the left table plus the matching rows from the right (NULL where there is no match). RIGHT JOIN is the opposite: all rows from the right table plus matches from the left. FULL JOIN returns all rows from both tables, with NULL where there is no match. Example: SELECT * FROM Orders o INNER JOIN Customers c ON o.customer_id = c.id.",
            "points": [
                ("A join combines rows from tables using a related column", ["combine", "related", "column", "common", "on "]),
                ("INNER JOIN returns only matching rows", ["inner"]),
                ("LEFT JOIN keeps all rows from the left table", ["left"]),
                ("RIGHT JOIN keeps all rows from the right table", ["right"]),
                ("FULL JOIN / NULL for non-matches / example", ["full", "null", "example", "select"]),
            ],
        },
        {
            "model": "Normalization is the process of organizing a database into well-structured tables to reduce data redundancy (duplicate data) and avoid insert, update and delete anomalies. It is done in steps called normal forms: 1NF (each column holds atomic values, no repeating groups), 2NF (1NF plus no partial dependency on part of the primary key), and 3NF (2NF plus no transitive dependency between non-key columns). The trade-off is that highly normalized data needs more joins, which can slow down reads.",
            "points": [
                ("Reduces data redundancy / duplicate data", ["redundan", "duplicate", "duplication"]),
                ("Avoids anomalies / improves data integrity", ["anomal", "integrity", "consisten"]),
                ("Normal forms: 1NF, 2NF, 3NF", ["1nf", "2nf", "3nf", "normal form", "first normal"]),
                ("Splits data into related tables", ["split", "divide", "separate", "tables", "relat"]),
                ("Trade-off: more joins / example", ["join", "trade", "example", "for instance", "slower"]),
            ],
        },
        {
            "model": "A subquery is a query nested inside another query (inside WHERE, FROM or SELECT). The inner query runs first and its result is used by the outer query. Example: SELECT name FROM Employees WHERE salary > (SELECT AVG(salary) FROM Employees); this returns employees who earn more than the average salary. Subqueries can return a single value, a list of values, or a table.",
            "points": [
                ("A query nested inside another query", ["nested", "inside", "inner", "within"]),
                ("The inner query runs first, its result is used by the outer query", ["outer", "first", "result"]),
                ("Used in WHERE / FROM / SELECT", ["where", "from", "select"]),
                ("Concrete example (e.g. salary above the average)", ["example", "avg", "average", "salary", "for instance"]),
                ("Can return a single value, a list or a table", ["single value", "list", "table", "multiple", "one value"]),
            ],
        },
        {
            "model": "An index is a database structure (usually a B-tree) that lets the database find rows quickly without scanning the whole table, similar to the index of a book. It speeds up SELECT queries, especially on columns used in WHERE, JOIN and ORDER BY. The trade-offs are that indexes use extra storage and slow down INSERT, UPDATE and DELETE because the index must also be updated. So create indexes on frequently searched columns, and avoid them on very small tables or on columns that change constantly.",
            "points": [
                ("An index speeds up searches / avoids a full table scan", ["fast", "speed", "quick", "scan", "search", "lookup"]),
                ("Data structure such as a B-tree / book index analogy", ["b-tree", "btree", "book", "structure", "pointer"]),
                ("Used on WHERE / JOIN / ORDER BY columns", ["where", "join", "order by", "column"]),
                ("Drawback: slows INSERT, UPDATE and DELETE", ["slow", "insert", "update", "delete", "write"]),
                ("Extra storage / when to use or avoid", ["storage", "space", "memory", "avoid", "small table", "when"]),
            ],
        },
    ],
    "DSA": [
        {
            "model": "An array stores elements in a contiguous block of memory, so you can access any element by index in O(1) time. But inserting or deleting in the middle is O(n) because elements must be shifted, and its size is usually fixed. A linked list stores elements as nodes, where each node holds data and a pointer to the next node, so elements are not contiguous. Insertion or deletion is O(1) if you already have the node, size is dynamic, but accessing an element takes O(n) because you must traverse from the head, and each node needs extra memory for the pointer.",
            "points": [
                ("Array: contiguous memory", ["contiguous", "continuous", "consecutive", "sequential memory"]),
                ("Array gives O(1) access by index", ["o(1)", "index", "random access", "direct access"]),
                ("Linked list: nodes with pointers", ["node", "pointer", "next", "link"]),
                ("Linked list: easy insertion/deletion, access is O(n)", ["insert", "delet", "o(n)", "traverse", "sequential access"]),
                ("Size: array is fixed, linked list is dynamic", ["dynamic", "fixed", "size", "resize"]),
            ],
        },
        {
            "model": "A stack follows LIFO (Last In, First Out): the last element added is the first one removed, using push and pop on one end (the top). Examples: undo feature, function call stack, browser back button. A queue follows FIFO (First In, First Out): elements are added at the rear (enqueue) and removed from the front (dequeue). Examples: a printer queue, a line at a ticket counter, and BFS traversal.",
            "points": [
                ("Stack follows LIFO", ["lifo", "last in"]),
                ("Queue follows FIFO", ["fifo", "first in"]),
                ("Stack operations: push and pop (one end, the top)", ["push", "pop", "top"]),
                ("Queue operations: enqueue and dequeue (rear and front)", ["enqueue", "dequeue", "front", "rear"]),
                ("Real-world examples", ["example", "undo", "printer", "line", "call stack", "for instance"]),
            ],
        },
        {
            "model": "BFS (Breadth-First Search) explores a graph level by level: it visits all neighbors of a node first before going deeper, and it uses a queue. It finds the shortest path in an unweighted graph. DFS (Depth-First Search) goes as deep as possible along one path before backtracking, and it uses a stack (or recursion). It is useful for cycle detection, topological sort and exploring all paths. Both run in O(V + E) time, but BFS can use more memory on wide graphs.",
            "points": [
                ("BFS explores level by level (neighbors first)", ["level", "breadth", "neighbor", "neighbour"]),
                ("BFS uses a queue", ["queue"]),
                ("DFS goes deep first and backtracks", ["depth", "deep", "backtrack"]),
                ("DFS uses a stack or recursion", ["stack", "recursion", "recursive"]),
                ("Use cases or complexity (shortest path, O(V+E))", ["shortest", "o(v", "cycle", "complexity", "time"]),
            ],
        },
        {
            "model": "A hash table stores key-value pairs. A hash function converts the key into an index (bucket) in an array, which gives average O(1) time for insert, search and delete. A collision happens when two different keys map to the same index. It is handled mainly by chaining (each bucket holds a linked list of entries) or open addressing (probe for the next free slot, using linear probing, quadratic probing or double hashing). A good hash function and a low load factor keep collisions rare.",
            "points": [
                ("Stores key-value pairs", ["key", "value"]),
                ("A hash function maps a key to an index (bucket)", ["hash function", "hash", "bucket", "index"]),
                ("Average O(1) insert/search/delete", ["o(1)", "constant", "fast"]),
                ("Collision = two keys map to the same index", ["collision", "same index", "same bucket"]),
                ("Collision handling: chaining or open addressing", ["chaining", "linked list", "open addressing", "probing"]),
            ],
        },
        {
            "model": "A Binary Search Tree (BST) is a binary tree where every node has at most two children, and for each node all values in the left subtree are smaller and all values in the right subtree are larger. To search, you compare the target with the current node and go left or right, which discards half of the tree at each step. For a balanced BST this takes O(log n) time. In the worst case (a skewed tree, like a linked list) it becomes O(n), which is why self-balancing trees such as AVL and Red-Black trees are used.",
            "points": [
                ("Binary tree: each node has at most two children", ["two children", "binary", "left", "right"]),
                ("Left subtree is smaller, right subtree is larger", ["smaller", "larger", "greater", "less than"]),
                ("Search compares and goes left or right (halves the tree)", ["compare", "half", "discard", "go left", "go right"]),
                ("O(log n) for a balanced tree", ["o(log", "log n", "logarithmic"]),
                ("Worst case O(n) / balanced trees (AVL, Red-Black)", ["o(n)", "skew", "worst", "avl", "red-black", "balanced"]),
            ],
        },
    ],
}

KB = {}
for _topic, _items in KB_LIST.items():
    for _q, _kb in zip(QUESTIONS[_topic], _items):
        KB[_q] = _kb


def local_evaluate(topic, question, answer):
    """Rule-based evaluation without internet (keyword matching)."""
    kb = KB.get(question)
    text = answer.lower()
    words = len(text.split())
    sentences = len([s for s in re.split(r"[.!?\n]+", text) if s.strip()])

    if kb:
        points, model = kb["points"], kb["model"]
    else:
        points, model = [("Main point", [])], "A model answer is not available for this question yet."

    matched = [p for p in points if p[1] and any(k in text for k in p[1])]
    missing = [p[0] for p in points if p not in matched]
    cov = len(matched) / len(points)

    def clamp(x):
        return max(0, min(10, int(round(x))))

    length_score = 2 if words < 5 else 4 if words < 15 else 6 if words < 35 else 8
    correctness = clamp(1 + 9 * cov)
    completeness = clamp(10 * cov)
    clarity = clamp(length_score + (1 if sentences >= 2 else 0))
    structure = clamp(2 + min(sentences, 4) + (2 if words >= 25 else 0))
    relevance = clamp(2 + 8 * min(1.0, cov * 1.6)) if matched else 2

    mistakes = []
    if not matched and words >= 3:
        mistakes.append("wrong_concept")
    if cov < 0.7:
        mistakes.append("incomplete")
    if words < 10:
        mistakes.append("unclear")
    if not any(k in text for k in ["example", "for instance", "e.g", "such as"]):
        mistakes.append("no_example")
    if not matched and words >= 15:
        mistakes.append("off_topic")

    def reason(score, good, bad):
        return good if score >= 7 else bad

    reasons = {
        "correctness": f"You covered {len(matched)} of {len(points)} key points. "
        + reason(correctness, "The concept is largely correct.", "Several key points are missing or the concept is incomplete."),
        "clarity": reason(clarity, "The answer is easy to understand.", "The answer is too short or unclear. Explain it in more detail."),
        "completeness": reason(completeness, "Most of the important points are covered.", "Several points are missing: " + ", ".join(missing[:3]) + "."),
        "structure": reason(structure, "The answer follows a logical order.", "Organize the answer into steps (definition first, then details, then an example)."),
        "relevance": reason(relevance, "The answer stays on topic.", "The answer seems far from the main topic of the question."),
    }

    steps = []
    for m in missing[:3]:
        steps.append(f"Study this point and write it in your own words: {m}")
    if "no_example" in mistakes:
        steps.append("Add a short real-world example to every answer.")
    if not steps:
        steps.append("Great job! Practice saying this answer aloud in under 1 minute.")
    steps[0] += "  (Note: the AI was busy, so this is offline rule-based feedback.)"

    return {
        "scores": {
            "correctness": correctness,
            "clarity": clarity,
            "completeness": completeness,
            "structure": structure,
            "relevance": relevance,
        },
        "reasons": reasons,
        "mistake_types": mistakes,
        "missing_points": missing,
        "model_answer": model,
        "improvement_steps": steps,
    }


# ---------------------------------------------------------------------------
# GEMINI
# ---------------------------------------------------------------------------
class GeminiBusy(Exception):
    pass


def call_gemini_once(prompt, api_key):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={api_key}"
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_gemini(prompt, api_key):
    last_error = "Unknown error"
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return call_gemini_once(prompt, api_key)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore")[:300]
            last_error = f"Gemini API error {e.code}: {detail}"
            if e.code in (400, 401, 403):
                raise RuntimeError(last_error)  # bad key, retrying will not help
        except (socket.timeout, TimeoutError, urllib.error.URLError) as e:
            last_error = f"Gemini is slow or the connection failed: {e}"
        print(f"[retry] attempt {attempt} failed: {last_error[:140]}")
        time.sleep(2)
    raise GeminiBusy(last_error)


def build_prompt(topic, question, answer):
    return f"""You are a strict but helpful interviewer for the topic: {topic}.
Question: {question}
Candidate answer: {answer}

Return ONLY valid JSON in exactly this format:
{{
  "scores": {{"correctness": 0, "clarity": 0, "completeness": 0, "structure": 0, "relevance": 0}},
  "reasons": {{"correctness": "...", "clarity": "...", "completeness": "...", "structure": "...", "relevance": "..."}},
  "mistake_types": ["choose from: wrong_concept, incomplete, unclear, no_example, off_topic"],
  "missing_points": ["important points the candidate missed"],
  "model_answer": "a good, complete ideal answer",
  "improvement_steps": ["2-3 concrete things to practice next"]
}}
Scores must be integers from 0 to 10. Write all reasons and text in clear, simple English."""


def evaluate(topic, question, answer, api_key):
    # typing "offline" as the key uses the offline evaluator directly
    if not api_key or api_key.strip().lower() == "offline":
        return local_evaluate(topic, question, answer)
    try:
        raw = call_gemini(build_prompt(topic, question, answer), api_key)
        raw = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except (GeminiBusy, json.JSONDecodeError, KeyError) as e:
        print(f"[fallback] Gemini failed ({str(e)[:100]}), using the offline evaluator")
        return local_evaluate(topic, question, answer)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, content_type="application/json"):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(os.path.join(HERE, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html")
            except FileNotFoundError:
                self._send(404, "index.html not found. Keep both files in the same folder.", "text/plain")
        elif self.path == "/api/questions":
            self._send(200, QUESTIONS)
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/evaluate":
            self._send(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            api_key = data.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
            if not str(data.get("answer", "")).strip():
                self._send(400, {"error": "The answer is empty."})
                return
            result = evaluate(
                data.get("topic", ""), data.get("question", ""), data["answer"], api_key
            )
            self._send(200, result)
        except RuntimeError as e:
            self._send(502, {"error": str(e)})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print("[server]", fmt % args)


if __name__ == "__main__":
    print(f"Server running at: http://localhost:{PORT}  (press Ctrl + C to stop)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
