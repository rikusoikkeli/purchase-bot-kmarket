# purchase-bot-kmarket

WHAT DOES THE CODE DO:

1. The program takes a shopping list (an example can be found from the file items_to_buy.py)

2. It goes to https://www.k-ruoka.fi/ and searches for every item in the shopping list

3. For every search, it chooses the least expensive variety to add to the cart. Except
if the least expensive variety costs more than price_constraint set in the shopping list. If that
happens, the item is skipped.

4. After shopping, it sends a summary of what happened to your chosen email address. What kind of
items were chosen, if something was skipped, etc.

WHY DID I CREATE THIS:

Honestly, shopping for groceries is the least exciting thing in the world. What I did every week was 
really simple: I wanted to buy the same items every time. Except different things were on sale on
different weeks. 

So sometimes I bought tomatoes, sometimes they were too expensive. Sometimes I bought salmon, sometimes 
it was too expensive. And I always wanted to buy the cheapest tomatoes and the cheapest salmon. 

I figured this to be a pretty simple algorithm. So I wrote code for it. And I scheduled it to run on my 
Jenkins server every week. What I have to do now is just log in to k-ruoka.fi, add how much I want to 
buy every item in my shopping cart, and approve of the purchase.

Saves so much time and effort every week. Maybe some money, too. And last but not least: unlike myself,
the bot never forgets to bring anything from the store.
