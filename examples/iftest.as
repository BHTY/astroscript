set a = 2
set b = 1

if (a == b)
    echo "A and B are both " + $a
    endblk
else if (b == 1)
    if (a == 2)
        echo "A is 2"
        endblk
    endif
    echo "B is 1"
    endblk
else
    echo "Everything is false! Mwahahahaha!"
    endblk
endif

echo "The if statements are complete."
