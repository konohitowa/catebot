# CateBot Information

## FAQ

### What is CateBot?
Catebot is a reddit bot that is triggered by Catechism of the Catholic Church (CCC) paragraph references in reddit comments. It posts the contents of the CCC selection as a reply to the comment that contained the CCC paragraph reference.

### Where is it currently being used?
CateBot is currently running on the following subreddits:

* [/r/Catholicism](http://www.reddit.com/r/Catholicism/)
* [/r/Christianity](http://www.reddit.com/r/Christianity/)

### How do I use it?
If you want CateBot to quote a Catechism paragraph from your comment, simply surround the paragraph number in brackets and precede the number with CCC ([CCC 1234]). CateBot also understands a few slightly more advanced syntaxes. To start with, the CCC tag is case-insensitive, so [ccc 1234] would work just as well. In addition, you aren't limited to just one paragraph: you can specific multiple paragraphs separated by commas, and you can specify a range of paragraphs using a hyphen.

### Can you give me some examples of how to use the bot?
Using the reference [ccc 1] would ask CateBot to quote the 1st paragraph of the CCC.

Multiple paragraphs such as [ccc 3,120,72] can also be requested.

And rather than using [ccc 2105,2106,2107] you could just specify a range using [ccc 2105-2107]. A range **must**
be in ascending order (i.e., [smallernumber - largernumber]).

And you can always mix and match like so: [ccc 3,2105-2107].

You don't _have_ to include the space after the ccc tag, but [ccc5] doesn't look nearly as clean. You can also include spaces after the commas, such as [ccc 3, 2105].

_Remember, the paragraph references can be located **ANYWHERE** in your comment!_

### What happens if I quote a non-existent paragraph of the CCC?
Catebot ignores it.

### How many paragraphs can I quote?
You are limited by the maximum size of a reddit response. The reddit API has a limit of 10,000 characters in
a post; Catebot arbitrarily lowers this 8,000 characters. If the response is larger than that, Catebot
lets you know and assembles a listing of links only rather than links with text. If this is also too large,
it links as many paragraphs as it can and then gives an additional message letting you know that you blew
that, too.

### Wait. I've counted the characters and I didn't hit the limit!
Look at the source instead; the links take up a fair amount of text.

### Why is the bot not responding to my comment?
This could be attributed to a few different things:
* Your paragraph reference doesn't follow the guidelines specified above.
* The bot is down temporarily for maintenance/updates.
* The bot is trying to keep up with commands (there is a 30 second sleep period between comment scan as well as some limits by reddit as to how frequently the bot can respond).
* Reddit isn't responding to the bot during the windows in which it scans. This should be a temporary situation that is dependent upon reddit load.

### How do you pronounce Catebot?
Like cate-chism. But, you know, with 'bot' in place of 'chism'.

### What should I do if I still have questions?
Just ask me! You can [contact me on reddit](http://www.reddit.com/message/compose/?to=kono_hito_wa).

### Is there any end matter to this FAQ?
Yes!

Okay - just kidding. I *would* link to thank the moderators of and contributors to [/r/Catholicsm](http://www.reddit.com/r/Catholicism) for putting up with my testing as well as generating test cases and suggestions/feedback. And a big thanks to [Matthieu Grieger](http://www.reddit.com/u/mgrieger) for open sourcing [versebot on github](http://github.com/matthieugrieger/versebot). If he hadn't done that, I highly doubt I would have had the ambition to build this from scratch and, if I had, it would have take me significantly longer.
