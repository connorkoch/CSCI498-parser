import java.util.ArrayList;
import java.util.Objects;

public class ProductionRule {
    public ArrayList<AlphabetCharacter> rhs;

    public ProductionRule() {
        this.rhs = new ArrayList<>();
    }

    public void addCharacterToRHS(AlphabetCharacter c) {
        rhs.add(c);
    }

    /**
     * Only a lambda production if it's ONLY L -> lambda
     * @return
     */
    public boolean isLambdaProduction() {
        return rhs.size() == 1 && rhs.get(0).isLambda();
    }

    /**
     * Returns true if *anything* on the RHS is not a nonterminal
     * @return
     */
    public boolean containsTerminal() {
        for (AlphabetCharacter c : rhs) {
            if (c.isNonTerminal() == false) {
                return true;
            }
        }

        return false;
    }

    @Override
    public String toString() {
        StringBuilder result = new StringBuilder("-> ");

        for (AlphabetCharacter c : rhs) {
            result.append(c).append(" ");
        }

        return result.toString();
    }

    @Override
    public int hashCode() {
        return this.toString().hashCode();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ProductionRule that = (ProductionRule) o;
        return Objects.equals(rhs, that.rhs);
    }
}
