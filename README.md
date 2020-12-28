# purchase-bot-kmarket

WHAT DOES THE CODE DO:

1. The program takes a shopping list (an example can be found from the file items_to_buy.py)

2. It goes to https://www.k-ruoka.fi/ and searches for every item

3. For every search, it chooses the least expensive item to add in the shopping cart
(if the price is not more than price_constraint set in the shopping list.

WHY DID I CREATE THIS:

Honestly, shopping for groceries is the least exciting thing in the world. What I did every week was 
really simple: I wanted to buy the same items every time. Except different things were on sale on
different weeks. 

So sometimes I bought tomatoes, sometimes they were too expensive. Sometimes I bought salmon, sometimes 
it was too expensive. And I always wanted to buy the cheapest tomatoes and the cheapest salmon. 

I figured this to be a pretty simple algorithm. So I wrote code for it. And I scheduled it to run on my 
Jenkins server every week. What I have to do now is just log in to k-ruoka.fi, add how much I want to 
buy every item in my shopping cart, and approve of the purchase.

Saves so much time and effort every week. Maybe some money, too. And last but not least, unlike myself,
the bot never forgets anything.
